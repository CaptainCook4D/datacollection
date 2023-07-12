import logging
import os
import pickle
import threading
from contextlib import contextmanager
from typing import List

import numpy as np
import redis
import cv2

from ..models.hololens_info import HololensInfo
from ..models.recording import Recording
from ..hololens import hl2ss
from ..hololens.hololens_rest_api import *
from ..utils.constants import Hololens_Constants as const
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


def create_directories(dir_path):
	if not os.path.exists(dir_path):
		os.makedirs(dir_path)


class StreamProcessor:
	
	def __init__(self, redis_pool, recording, port_to_stream, active_streams):
		self.redis_pool = redis_pool
		self.recording = recording
		self.port_to_stream = port_to_stream
		self.active_streams = active_streams
		self.enable_streams = True
		self.stream_threads = []
	
	def start_processing_streams(self):
		for stream_port in self.active_streams:
			stream_thread = threading.Thread(target=self._process_stream, args=(stream_port,))
			self.stream_threads.append(stream_thread)
		
		for stream_thread in self.stream_threads:
			stream_thread.start()
	
	def stop_processing_streams(self):
		self.enable_streams = False
		
		for stream_thread in self.stream_threads:
			stream_thread.join()


class Producer(StreamProcessor):
	
	def __init__(self, redis_pool, recording, port_to_stream, active_streams):
		super().__init__(redis_pool, recording, port_to_stream, active_streams)
		self.redis_pool = redis_pool
		self.recording = recording
		
		self.port_to_stream = port_to_stream
		self.active_streams = active_streams
		
		self.enable_streams = True
		self.stream_threads = []
		
		self.device_ip = self.recording.recording_info.hololens_info.device_ip
	
	# Currently we capture data from streams from only PHOTO VIDEO, DEPTH AHAT, SPATIAL INPUT, MICROPHONE
	# If the RAW images takes a lot of time to transfer
	# 1. Change the resolution of video frames and check
	# 2. Else use encoded format for frames
	# 3. Else move to REST-API approach
	def _fetch_stream_client(self, stream_port):
		stream_client = None
		if stream_port == hl2ss.StreamPort.PHOTO_VIDEO:
			stream_client = hl2ss.rx_pv(
				self.device_ip, stream_port, hl2ss.ChunkSize.PHOTO_VIDEO, hl2ss.StreamMode.MODE_1,
				const.PV_FRAME_WIDTH, const.PV_FRAME_HEIGHT,
				const.PV_FRAMERATE, const.PV_VIDEO_PROFILE_RAW, const.PV_VIDEO_BITRATE_RAW
			)
		elif stream_port == hl2ss.StreamPort.RM_DEPTH_AHAT:
			stream_client = hl2ss.rx_rm_depth_ahat(
				self.device_ip, stream_port, hl2ss.ChunkSize.RM_DEPTH_AHAT, hl2ss.StreamMode.MODE_1,
				const.AHAT_PROFILE_RAW, const.AHAT_BITRATE_RAW
			)
		elif stream_port == hl2ss.StreamPort.MICROPHONE:
			stream_client = hl2ss.rx_microphone(
				self.device_ip, stream_port, hl2ss.ChunkSize.MICROPHONE, const.AUDIO_PROFILE_DECODED
			)
		elif stream_port == hl2ss.StreamPort.SPATIAL_INPUT:
			stream_client = hl2ss.rx_si(
				self.device_ip, stream_port, hl2ss.ChunkSize.SPATIAL_INPUT
			)
		elif stream_port == hl2ss.StreamPort.RM_IMU_ACCELEROMETER:
			stream_client = hl2ss.rx_rm_imu(
				self.device_ip, stream_port, hl2ss.ChunkSize.RM_IMU_ACCELEROMETER, hl2ss.StreamMode.MODE_1
			)
		elif stream_port == hl2ss.StreamPort.RM_IMU_GYROSCOPE:
			stream_client = hl2ss.rx_rm_imu(
				self.device_ip, stream_port, hl2ss.ChunkSize.RM_IMU_GYROSCOPE, hl2ss.StreamMode.MODE_1
			)
		elif stream_port == hl2ss.StreamPort.RM_IMU_MAGNETOMETER:
			stream_client = hl2ss.rx_rm_imu(
				self.device_ip, stream_port, hl2ss.ChunkSize.RM_IMU_MAGNETOMETER, hl2ss.StreamMode.MODE_1
			)
		return stream_client
	
	def _process_stream(self, stream_port):
		logger.info(f"Configuring {self.port_to_stream[stream_port]} Producer for recording {self.recording.__str__()}")
		
		stream_client = self._fetch_stream_client(stream_port)
		
		if stream_client is None:
			logger.info(f'Stream client is not configured for stream {self.port_to_stream[stream_port]}')
			return
		
		stream_client.open()
		
		logger.info(f"Created stream client for {self.port_to_stream[stream_port]}")
		
		# Create a redis client and push the stream data to the queue named stream_port continuously
		stream_redis_client = redis.Redis(connection_pool=self.redis_pool)
		
		stream_queue_name = self.port_to_stream[stream_port]
		
		while self.enable_streams:
			stream_data = stream_client.get_next_packet()
			stream_redis_client.lpush(stream_queue_name, bytes(hl2ss.pack_packet(stream_data)))
		
		logger.info(f"Closing stream client for {self.port_to_stream[stream_port]}")
		stream_client.close()


class FileWriter:
	
	def __init__(self, file_path, file_extension: str):
		self._opened_file = open(file_path, 'ab')
		self._file_extension = file_extension
	
	def write(self, stream_packet):
		if self._file_extension == '.pkl':
			pickle.dump(stream_packet, self._opened_file)
		else:
			self._opened_file.write(stream_packet)
	
	def close(self):
		self._opened_file.close()


# TODO:
# 1. Check if every stream can be written into binary format
# 2. Check with synchronization service
# 3. Come back and change the code later

class Consumer(StreamProcessor):
	
	def __init__(self, redis_pool, recording, port_to_stream, active_streams, port_to_dir):
		super().__init__(redis_pool, recording, port_to_stream, active_streams)
		self.redis_pool = redis_pool
		self.recording = recording
		
		self.port_to_stream = port_to_stream
		self.active_streams = active_streams
		self.port_to_dir = port_to_dir
		
		self.store_frame_as_binary = False
		self.enable_streams = True
		self.stream_threads = []
	
	def _process_stream_data(self, stream_port, stream_data, **kwargs):
		# Unpack the raw data
		# This packet has timestamp, payload and necessary pose information
		stream_packet = hl2ss.unpack_packet(stream_data)
		stream_name = self.port_to_stream[stream_port]

		if stream_port == hl2ss.StreamPort.PHOTO_VIDEO:
			# Here we need to save
			# 1. Pose information
			kwargs[const.PV_POSE_WRITER].write((stream_packet.timestamp, stream_packet.pose))
			
			# 2. PV payload information - decoded
			pv_file_name = f'{self.recording.get_recording_id()}_{stream_name}_{stream_packet.timestamp}.jpg'
			pv_file_path = os.path.join(kwargs[const.PV_DATA_DIRECTORY], pv_file_name)
			
			frame_nv12 = np.frombuffer(
				stream_packet.payload, dtype=np.uint8,
				count=int((const.PV_STRIDE * const.PV_FRAME_HEIGHT * 3) / 2)
			).reshape((int(const.PV_FRAME_HEIGHT * 3 / 2), const.PV_STRIDE))
			frame_bgr = cv2.cvtColor(frame_nv12[:, :const.PV_FRAME_WIDTH], cv2.COLOR_YUV2BGR_NV12)
			cv2.imwrite(pv_file_path, frame_bgr)

		elif stream_port == hl2ss.StreamPort.RM_DEPTH_AHAT:
			# Here we need to save
			# 1. Pose information
			# np.savez(os.path.join(stream_directory, kwargs[DEPTH_AHAT_POSE_FILE_NAME]), stream_packet.pose)
			kwargs[const.DEPTH_AHAT_POSE_WRITER].write((stream_packet.timestamp, stream_packet.pose))
			
			# 2. AHAT AB information
			ab_file_name = f'{self.recording.get_recording_id()}_{stream_name}_ab_{stream_packet.timestamp}.png'
			ab_file_path = os.path.join(kwargs[const.DEPTH_AHAT_AB_DATA_DIRECTORY], ab_file_name)
			
			ab_data = np.frombuffer(
				stream_packet.payload, dtype=np.uint16,
				offset=hl2ss.Parameters_RM_DEPTH_AHAT.PIXELS * hl2ss._SIZEOF.WORD,
				count=hl2ss.Parameters_RM_DEPTH_AHAT.PIXELS
			).reshape(hl2ss.Parameters_RM_DEPTH_AHAT.SHAPE)
			cv2.imwrite(ab_file_path, ab_data)
			
			# 3. AHAT depth information
			depth_file_name = f'{self.recording.get_recording_id()}_{stream_name}_depth_{stream_packet.timestamp}.png'
			depth_file_path = os.path.join(kwargs[const.DEPTH_AHAT_DEPTH_DATA_DIRECTORY], depth_file_name)
			
			depth_data = np.frombuffer(
				stream_packet.payload, dtype=np.uint16, count=hl2ss.Parameters_RM_DEPTH_AHAT.PIXELS
			).reshape(hl2ss.Parameters_RM_DEPTH_AHAT.SHAPE)
			cv2.imwrite(depth_file_path, depth_data)

		elif stream_port == hl2ss.StreamPort.MICROPHONE:
			kwargs[const.MICROPHONE_DATA_WRITER].write(
				(stream_packet.timestamp, stream_packet.payload)
			)

		elif stream_port == hl2ss.StreamPort.SPATIAL_INPUT:
			kwargs[const.SPATIAL_DATA_WRITER].write((stream_packet.timestamp, stream_packet.payload))

		elif stream_port == hl2ss.StreamPort.RM_IMU_ACCELEROMETER:
			kwargs[const.IMU_ACCELEROMETER_DATA_WRITER].write(
				(stream_packet.timestamp, (stream_packet.payload, stream_packet.pose))
			)
		elif stream_port == hl2ss.StreamPort.RM_IMU_GYROSCOPE:
			kwargs[const.IMU_GYROSCOPE_DATA_WRITER].write(
				(stream_packet.timestamp, (stream_packet.payload, stream_packet.pose))
			)
		elif stream_port == hl2ss.StreamPort.RM_IMU_MAGNETOMETER:
			kwargs[const.IMU_MAGNETOMETER_DATA_WRITER].write(
				(stream_packet.timestamp, (stream_packet.payload, stream_packet.pose))
			)
	
	def _fetch_stream_kwargs(self, stream_port):
		stream_directory = self.port_to_dir[stream_port]
		stream_name = self.port_to_stream[stream_port]
		kwargs = {}
		if stream_port == hl2ss.StreamPort.PHOTO_VIDEO:
			# Here we need to save
			# 1. Pose information
			# 2. PV payload information
			stream_file_path = os.path.join(
				stream_directory, f'{self.recording.get_recording_id()}_{stream_name}_pose.pkl'
			)
			kwargs[const.PV_POSE_WRITER] = FileWriter(stream_file_path, file_extension=".pkl")
			kwargs[const.PV_DATA_DIRECTORY] = os.path.join(stream_directory, const.FRAMES)
		elif stream_port == hl2ss.StreamPort.RM_DEPTH_AHAT:
			# Here we need to save
			# 1. Pose information
			# 2. AHAT AB information
			# 3. AHAT depth information
			stream_file_path = os.path.join(
				stream_directory, f'{self.recording.get_recording_id()}_{stream_name}_pose.pkl'
			)
			kwargs[const.DEPTH_AHAT_POSE_WRITER] = FileWriter(stream_file_path, file_extension=".pkl")
			kwargs[const.DEPTH_AHAT_AB_DATA_DIRECTORY] = os.path.join(stream_directory, const.AB)
			kwargs[const.DEPTH_AHAT_DEPTH_DATA_DIRECTORY] = os.path.join(stream_directory, const.DEPTH)
		elif stream_port == hl2ss.StreamPort.MICROPHONE:
			# Here we need to save
			# 1. Dump of the decoded microphone data into a pickle file
			# TODO: Raw Microphone data storing in bytes has weird background noise
			stream_file_path = os.path.join(stream_directory, f'{self.recording.get_recording_id()}_{stream_name}.pkl')
			kwargs[const.MICROPHONE_DATA_WRITER] = FileWriter(stream_file_path, file_extension=".pkl")
		elif stream_port == hl2ss.StreamPort.SPATIAL_INPUT:
			# Here we need to save
			# 1. Dump of the spatial data into a pickle file
			stream_file_path = os.path.join(stream_directory, f'{self.recording.get_recording_id()}_{stream_name}.pkl')
			kwargs[const.SPATIAL_DATA_WRITER] = FileWriter(stream_file_path, file_extension=".pkl")

		# IMU Data Writers
		elif stream_port == hl2ss.StreamPort.RM_IMU_ACCELEROMETER:
			# Here we need to save
			# 1. Dump of the IMU accelerometer data into a pickle file
			stream_file_path = os.path.join(stream_directory, f'{self.recording.get_recording_id()}_{stream_name}.pkl')
			kwargs[const.IMU_ACCELEROMETER_DATA_WRITER] = FileWriter(stream_file_path, file_extension=".pkl")
		elif stream_port == hl2ss.StreamPort.RM_IMU_GYROSCOPE:
			# Here we need to save
			# 1. Dump of the IMU gyroscope data into a pickle file
			stream_file_path = os.path.join(stream_directory, f'{self.recording.get_recording_id()}_{stream_name}.pkl')
			kwargs[const.IMU_GYROSCOPE_DATA_WRITER] = FileWriter(stream_file_path, file_extension=".pkl")
		elif stream_port == hl2ss.StreamPort.RM_IMU_MAGNETOMETER:
			# Here we need to save
			# 1. Dump of the IMU magnetometer data into a pickle file
			stream_file_path = os.path.join(stream_directory, f'{self.recording.get_recording_id()}_{stream_name}.pkl')
			kwargs[const.IMU_MAGNETOMETER_DATA_WRITER] = FileWriter(stream_file_path, file_extension=".pkl")
		
		return kwargs
	
	def _process_stream(self, stream_port):
		stream_name = self.port_to_stream[stream_port]
		
		logger.log(logging.INFO, f"Configuring {stream_name} Consumer for recording {self.recording.__str__()}")
		
		# Create a redis client and push the stream data to the queue named stream_port continuously
		stream_redis_client = redis.Redis(connection_pool=self.redis_pool)
		done_processing = False
		
		kwargs = self._fetch_stream_kwargs(stream_port)
		
		while True:
			stream_data = stream_redis_client.brpop([stream_name], timeout=3)
			
			if stream_data is None:
				# Finished processing of the streams
				if not self.enable_streams:
					done_processing = True
					logger.log(
						logging.INFO,
						f"Finished {stream_name} Consumer processing for recording {self.recording.__str__()}"
					)
				break
			else:
				# Convert the bytes received from stream data into byte array
				self._process_stream_data(stream_port, bytearray(stream_data[1]), **kwargs)
		
		if not done_processing:
			# Might be a temporary hold on the data, can come back in sometime
			# So make the process recursive
			logger.log(
				logging.INFO,
				f"Reached Timeout {self.port_to_stream[stream_port]} "
				f"Consumer but stream data is not yet done, so initialized processing again"
			)
			self._process_stream(stream_port)
		else:
			if stream_port == hl2ss.StreamPort.MICROPHONE:
				kwargs[const.MICROPHONE_DATA_WRITER].close()
			elif stream_port == hl2ss.StreamPort.SPATIAL_INPUT:
				kwargs[const.SPATIAL_DATA_WRITER].close()
			elif stream_port == hl2ss.StreamPort.RM_DEPTH_AHAT:
				kwargs[const.DEPTH_AHAT_POSE_WRITER].close()
			elif stream_port == hl2ss.StreamPort.PHOTO_VIDEO:
				kwargs[const.PV_POSE_WRITER].close()
			elif stream_port == hl2ss.StreamPort.RM_IMU_ACCELEROMETER:
				kwargs[const.IMU_ACCELEROMETER_DATA_WRITER].close()
			elif stream_port == hl2ss.StreamPort.RM_IMU_GYROSCOPE:
				kwargs[const.IMU_GYROSCOPE_DATA_WRITER].close()
			elif stream_port == hl2ss.StreamPort.RM_IMU_MAGNETOMETER:
				kwargs[const.IMU_MAGNETOMETER_DATA_WRITER].close()
			return


class HololensService:
	
	def __init__(self):
		self.rm_enable = True
		self.is_recording = False
		self.lock = threading.Lock()
		
		self.redis_pool = redis.ConnectionPool(host=const.REDIS_HOST, port=const.REDIS_PORT)
		
		# # Flush all the keys currently present in the database
		self.redis_connection = redis.Redis(connection_pool=self.redis_pool)
		self.redis_connection.flushdb()
	
	@staticmethod
	def save_hololens2_info(ip_address, folder_path, client_rc):
		host_name = get_hostname(ip_address)
		utc_offset = client_rc.get_utc_offset(32)
		logger.info(f"Hololens2 ID: {host_name}")
		logger.info(f"Hololens2 Offset: {utc_offset}")
		with open(os.path.join(folder_path, 'Hololens2Info.dat'), 'w+') as f:
			f.write(f"Hololens2 Name: {host_name}\n")
			f.write(f"HL2 UTC Offset: {utc_offset}")
		logger.info('QPC timestamp to UTC offset is {offset} hundreds of nanoseconds'.format(offset=utc_offset))
	
	def _init_params(
			self,
			recording: Recording,
			active_streams: List[int],
	):
		self.recording = recording
		self.device_ip = self.recording.recording_info.hololens_info.device_ip
		self.device_name = get_hostname(self.device_ip)
		
		self.rec_data_dir = os.path.join(self.data_dir, self.recording.id)
		self.port_to_dir = {
			hl2ss.StreamPort.PHOTO_VIDEO: os.path.join(self.rec_data_dir, const.PHOTOVIDEO),
			hl2ss.StreamPort.MICROPHONE: os.path.join(self.rec_data_dir, const.MICROPHONE),
			hl2ss.StreamPort.RM_DEPTH_AHAT: os.path.join(self.rec_data_dir, const.DEPTH_AHAT),
			hl2ss.StreamPort.SPATIAL_INPUT: os.path.join(self.rec_data_dir, const.SPATIAL),
			hl2ss.StreamPort.RM_IMU_ACCELEROMETER: os.path.join(self.rec_data_dir, const.IMU),
			hl2ss.StreamPort.RM_IMU_GYROSCOPE: os.path.join(self.rec_data_dir, const.IMU),
			hl2ss.StreamPort.RM_IMU_MAGNETOMETER: os.path.join(self.rec_data_dir, const.IMU),
			hl2ss.StreamPort.RM_VLC_LEFTFRONT: os.path.join(self.rec_data_dir, const.VLC_LEFTFRONT),
			hl2ss.StreamPort.RM_VLC_LEFTLEFT: os.path.join(self.rec_data_dir, const.VLC_LEFTLEFT),
			hl2ss.StreamPort.RM_VLC_RIGHTFRONT: os.path.join(self.rec_data_dir, const.VLC_RIGHTFRONT),
			hl2ss.StreamPort.RM_VLC_RIGHTRIGHT: os.path.join(self.rec_data_dir, const.VLC_RIGHTRIGHT),
			hl2ss.StreamPort.RM_DEPTH_LONGTHROW: os.path.join(self.rec_data_dir, const.DEPTH_LT),
		}
		
		self.port_to_stream = {
			hl2ss.StreamPort.RM_DEPTH_AHAT: const.DEPTH_AHAT,
			hl2ss.StreamPort.PHOTO_VIDEO: const.PHOTOVIDEO,
			hl2ss.StreamPort.MICROPHONE: const.MICROPHONE,
			hl2ss.StreamPort.SPATIAL_INPUT: const.SPATIAL,
			hl2ss.StreamPort.RM_DEPTH_LONGTHROW: const.DEPTH_LT,
			hl2ss.StreamPort.RM_IMU_MAGNETOMETER: const.IMU_MAGNETOMETER,
			hl2ss.StreamPort.RM_IMU_GYROSCOPE: const.IMU_GYROSCOPE,
			hl2ss.StreamPort.RM_IMU_ACCELEROMETER: const.IMU_ACCELEROMETER,
			hl2ss.StreamPort.RM_VLC_LEFTLEFT: const.VLC_LEFTLEFT,
			hl2ss.StreamPort.RM_VLC_LEFTFRONT: const.VLC_LEFTFRONT,
			hl2ss.StreamPort.RM_VLC_RIGHTRIGHT: const.VLC_RIGHTRIGHT,
			hl2ss.StreamPort.RM_VLC_RIGHTFRONT: const.VLC_RIGHTFRONT
		}
		
		self.active_streams = active_streams
		
		for port in self.active_streams:
			create_directories(self.port_to_dir[port])
			if (port == hl2ss.StreamPort.RM_DEPTH_AHAT) or (port == hl2ss.StreamPort.RM_DEPTH_LONGTHROW):
				create_directories(os.path.join(self.port_to_dir[port], const.AB))
				create_directories(os.path.join(self.port_to_dir[port], const.DEPTH))
			if port == hl2ss.StreamPort.PHOTO_VIDEO:
				create_directories(os.path.join(self.port_to_dir[port], const.FRAMES))
		
		# Start PV
		self.client_rc = hl2ss.ipc_rc(self.device_ip, hl2ss.IPCPort.REMOTE_CONFIGURATION)
		self.client_rc.open()
		
		if hl2ss.StreamPort.PHOTO_VIDEO in self.active_streams:
			hl2ss.start_subsystem_pv(self.device_ip, hl2ss.StreamPort.PHOTO_VIDEO)
			self.client_rc.wait_for_pv_subsystem(True)
	
	def _start_record_sensor_streams(self, recording: Recording, active_streams: List[int]):
		# Initialize all Parameters, Producers, Consumers, Display Map, Writer Map
		logger.info("Initializing parameters")
		self._init_params(recording, active_streams)
		HololensService.save_hololens2_info(self.device_ip, self.rec_data_dir, self.client_rc)
		
		self.producer = Producer(self.redis_pool, self.recording, self.port_to_stream, self.active_streams)
		self.producer.start_processing_streams()
		
		self.consumer = Consumer(self.redis_pool, self.recording, self.port_to_stream, self.active_streams,
								 self.port_to_dir)
		self.consumer.start_processing_streams()
		
		while self.rm_enable:
			time.sleep(10)
	
	def _stop_record_sensor_streams(self):
		
		logger.log(logging.INFO, "Stopping all record streams")
		
		self.producer.stop_processing_streams()
		self.consumer.stop_processing_streams()
		
		# Stopping PV systems
		if hl2ss.StreamPort.PHOTO_VIDEO in self.active_streams:
			hl2ss.stop_subsystem_pv(self.device_ip, hl2ss.StreamPort.PHOTO_VIDEO)
			self.client_rc.wait_for_pv_subsystem(False)
		
		self.client_rc.close()
		
		logger.log(logging.INFO, "Stopped all systems")
	
	def fetch_active_streams(self, recording: Recording):
		
		hololens_info: HololensInfo = recording.recording_info.hololens_info
		active_streams = []
		
		if hololens_info.pv:
			active_streams.append(hl2ss.StreamPort.PHOTO_VIDEO)
		
		if hololens_info.spatial:
			active_streams.append(hl2ss.StreamPort.SPATIAL_INPUT)
		
		if hololens_info.depth_ahat:
			active_streams.append(hl2ss.StreamPort.RM_DEPTH_AHAT)

		if hololens_info.imu:
			active_streams.append(hl2ss.StreamPort.RM_IMU_ACCELEROMETER)
			active_streams.append(hl2ss.StreamPort.RM_IMU_GYROSCOPE)
			active_streams.append(hl2ss.StreamPort.RM_IMU_MAGNETOMETER)
		
		if hololens_info.mc:
			active_streams.append(hl2ss.StreamPort.MICROPHONE)
		
		return active_streams
	
	def start_recording(self, recording: Recording, folder_path, is_mrc=False):
		
		active_streams = self.fetch_active_streams(recording)
		
		self.data_dir = folder_path
		
		if active_streams is None:
			active_streams = [hl2ss.StreamPort.RM_DEPTH_AHAT, hl2ss.StreamPort.SPATIAL_INPUT]
		
		if self.is_recording:
			logger.error("Already a process is recording videos")
			return
		if is_mrc:
			logger.info("Starting MRC recording")
			start_mrc(recording.recording_info.hololens_info.device_ip)
		
		logger.log(logging.INFO, "Starting a process to record videos")
		self.is_recording = True
		self._start_record_sensor_streams(recording, active_streams)
	
	def stop_recording(self, is_mrc=False):
		if not self.is_recording:
			print("Not recording")
			return
		
		if is_mrc:
			device_ip = self.recording.recording_info.hololens_info.device_ip
			stop_mrc(device_ip)
			time.sleep(3)
			download_most_recent_mrc_file(device_ip, self.rec_data_dir, self.recording.id)
		self.is_recording = False
		self._stop_record_sensor_streams()
