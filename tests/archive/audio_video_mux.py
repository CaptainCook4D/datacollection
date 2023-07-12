import os
import sys

import threading
import time
import logging

import pickle
import av
import cv2
import queue

from fractions import Fraction

from datacollection.user_app.backend.hololens import hl2ss
from datacollection.user_app.backend.models.recording import Recording
from datacollection.user_app.backend.constants import *

logging.basicConfig(filename='raw_upload.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logging.warning('Started Audio Video Muxing Service')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def add_to_sys_path():
	def add_path(path):
		if path not in sys.path:
			sys.path.insert(0, path)
	
	this_dir = os.path.dirname(__file__)
	
	lib_path = os.path.join(this_dir, "../backend")
	add_path(lib_path)


class AudioVideoMuxer:
	
	def __init__(self, data_directory, recording: Recording):
		self.tsfirst = None
		self.muxing_thread_list = []
		self.time_base = Fraction(1, hl2ss.TimeBase.HUNDREDS_OF_NANOSECONDS)
		
		self.lock = threading.Lock()
		self.rm_pv_enable = True
		self.packet_queue = queue.PriorityQueue()
		
		self.recording = recording
		self.data_directory = data_directory
		self.recording_id = self.recording.get_recording_id()
		
		self.video_directory = os.path.join(self.data_directory, "pv")
		self.audio_directory = os.path.join(self.data_directory, "mc")
	
	# self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')  # MJPG # case-sensitive Codecs
	# self.vlc_fourcc = cv2.VideoWriter_fourcc(*'H264')  # mp4v, H264, DIVX # case-sensitive Codecs
	
	def process_video(self, output_container, video_profile=PV_VIDEO_PROFILE_DECODED, video_frame_rate=PV_FRAMERATE,
	                  frame_extension=".jpg", timestamp_index=-1, video_decode=PV_VIDEO_DECODE,
	                  is_partial=False, start_timestamp=None, end_timestamp=None):
		
		# 1. Fetch list of images in a directory
		# 2. Loop through all images and store corresponding timestamps and encoded payload
		stream_video = output_container.add_stream(hl2ss.get_video_codec_name(video_profile), rate=video_frame_rate)
		codec_video = av.CodecContext.create(hl2ss.get_video_codec_name(video_profile), 'r')
		
		extension_length = len(frame_extension)
		frame_list = os.listdir(self.video_directory)
		frame_list = [frame for frame in frame_list if frame.endswith(frame_extension)]
		frame_list.sort(key=lambda x: int(((x[:-extension_length]).split("_"))[timestamp_index]))
		
		logger.log(logging.INFO, "Started Video Processing")
		for frame_idx, pv_frame_name in enumerate(frame_list):
			pv_frame_path = os.path.join(self.video_directory, pv_frame_name)
			
			pv_frame_array = cv2.imread(pv_frame_path)
			pv_timestamp = int(((pv_frame_name[:-extension_length]).split("_"))[timestamp_index])
			
			if is_partial:
				if pv_timestamp < start_timestamp or pv_timestamp > end_timestamp:
					continue
			
			self.lock.acquire()
			if self.tsfirst is None:
				self.tsfirst = pv_timestamp
			self.lock.release()
			
			pv_frame_decoded = av.VideoFrame.from_ndarray(pv_frame_array, format=video_decode)
			
			for packet in stream_video.encode(pv_frame_decoded):
				packet.stream = stream_video
				packet.pts = pv_timestamp - self.tsfirst
				packet.dts = packet.pts
				packet.time_base = self.time_base
				
				self.packet_queue.put((packet.pts, packet))
			
			if frame_idx % 1000 == 0:
				logger.log(logging.INFO, f"Processed '{frame_idx}' video frames")
	
	def process_audio(self, output_container, audio_profile=AUDIO_PROFILE_DECODED, audio_frame_rate=AUDIO_FRAME_RATE,
	                  is_partial=False, start_timestamp=None, end_timestamp=None):
		
		stream_audio = output_container.add_stream(hl2ss.get_audio_codec_name(audio_profile), rate=audio_frame_rate)
		codec_audio = av.CodecContext.create(hl2ss.get_audio_codec_name(audio_profile), 'r')
		
		mc_stream_file_name = f"{self.recording_id}.pkl"
		mc_stream_file_path = os.path.join(self.audio_directory, mc_stream_file_name)
		
		logger.log(logging.INFO, "Began Audio Processing")
		while self.tsfirst is None:
			time.sleep(0.3)
		
		logger.log(logging.INFO, "Started Audio Processing")
		# Load the pickle file
		mc_frame_idx = 0
		with open(mc_stream_file_path, 'rb') as mc_file:
			while True:
				try:
					mc_frame = pickle.load(mc_file)
					timestamp = int(mc_frame.timestamp)
					
					if is_partial:
						if timestamp < start_timestamp or timestamp > end_timestamp:
							continue
					
					if self.tsfirst is None:
						self.tsfirst = timestamp
					for packet in codec_audio.parse(mc_frame.payload):
						packet.stream = stream_audio
						packet.pts = timestamp - self.tsfirst
						packet.dts = packet.pts
						packet.time_base = self.time_base
						self.packet_queue.put((packet.pts, packet))
					
					mc_frame_idx += 1
					
					if mc_frame_idx % 1000 == 0:
						logger.log(logging.INFO, f"Processed '{mc_frame_idx}' audio frames")
				
				except EOFError:
					break
	
	def mux_pv_audio(self, output_container):
		logger.log(logging.INFO, "Configuring muxing")
		while self.rm_pv_enable:
			q_size = self.packet_queue.qsize()
			
			if q_size == 0:
				self.rm_pv_enable = False
				break
			
			if q_size % 500 == 0:
				logger.log(logging.INFO, f"Queue has '{q_size}' frames in it")
			
			ts, packet = self.packet_queue.get()
			output_container.mux(packet)
		
		logger.log(logging.INFO, "Stopped muxing")
		output_container.close()
	
	def reset_params(self):
		self.rm_pv_enable = True
		self.tsfirst = None
	
	def start_muxing_sync(self, start_timestamp=None, end_timestamp=None):
		
		is_partial = False
		muxed_file_name = f'{self.recording_id}.mp4'
		
		if start_timestamp is not None and end_timestamp is not None:
			muxed_file_name = f'{self.recording_id}_{start_timestamp}_{end_timestamp}.mp4'
			is_partial = True
		
		output_container = av.open(muxed_file_name, 'w')
		
		logger.log(logging.INFO, "Started synchronized audio-video muxing")
		self.process_video(output_container, is_partial=is_partial)
		logger.log(logging.INFO, "Added video frames to the Priority Queue")
		self.process_audio(output_container, is_partial=is_partial)
		logger.log(logging.INFO, "Added audio frames to the Priority Queue")
		self.mux_pv_audio(output_container)
	
	def start_muxing_async(self):
		pv_thread = threading.Thread(target=self.process_video)
		mc_thread = threading.Thread(target=self.process_audio)
		mux_thread = threading.Thread(target=self.mux_pv_audio)
		
		muxing_threads = [pv_thread, mc_thread, mux_thread]
		
		for thread in muxing_threads:
			thread.start()


def mux_directory(data_directory):
	recipe_list = os.listdir(data_directory)
	recipe_list.sort(key=lambda x: ((x.split("_"))[0]))
	
	for recipe_name in recipe_list:
		recording_arguments = recipe_name.split("_")
		recording_instance = Recording(recording_arguments[0], recording_arguments[1], recording_arguments[2],
		                               recording_arguments[3], False)
		
		logger.log(logging.INFO, f"Started synchronized audio-video muxing for recording {recording_arguments[0]}")
		
		mav = AudioVideoMuxer(data_directory, recording_instance)
		mav.start_muxing_sync()


if __name__ == '__main__':
	# recording_instance = Recording("EggSandwich", "PL2", "P5", "R1", False)
	# data_parent_directory = "/home/ptg/CODE/DATA/data_2022_02_11"
	# recording_instance.set_device_ip('192.168.0.117')
	#
	# mav = MuxAudioVideo(data_parent_directory, recording_instance)
	# mav.start_muxing_sync()
	
	data_parent_directory = "/home/ptg/CODE/DATA/data_2022_02_11"
	mux_directory(data_parent_directory)
