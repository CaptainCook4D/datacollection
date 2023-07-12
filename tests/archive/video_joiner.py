import logging
import os
import sys
from fractions import Fraction

import av
import cv2

from datacollection.user_app.backend.app.hololens import hl2ss

logging.basicConfig(filename='raw_upload.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logging.warning('Started Audio Video Muxing Service')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def add_to_sys_path():
	def add_path(path):
		if path not in sys.path:
			sys.path.insert(0, path)
	
	this_dir = os.path.dirname(__file__)
	
	# Add lib to PYTHONPATH
	lib_path = os.path.join(this_dir, "../backend")
	add_path(lib_path)


class VideoJoiner:

	def __init__(self, data_directory, recording):
		self.tsfirst = None
		self.recording = recording
		self.time_base = Fraction(1, hl2ss.TimeBase.HUNDREDS_OF_NANOSECONDS)

		self.recording_id = self.recording.get_recording_id()
		self.data_directory = os.path.join(data_directory, self.recording_id)
		self.video_directory = os.path.join(self.data_directory, "pv")

		self.codec_video = av.CodecContext.create(hl2ss.get_video_codec_name(PV_VIDEO_PROFILE_DECODED), 'r')

		self.video_name = f'{self.recording_id}_video.mp4'
		self.container = av.open(self.video_name, 'w')
		self.stream_video = self.container.add_stream(hl2ss.get_video_codec_name(PV_VIDEO_PROFILE_DECODED), rate=PV_FRAMERATE)

	def join_video(self, frame_extension=".jpg", timestamp_index=-1):
		extension_length = len(frame_extension)
		frame_list = os.listdir(self.video_directory)
		frame_list = [frame for frame in frame_list if frame.endswith(frame_extension)]
		frame_list.sort(key=lambda x: int(((x[:-extension_length]).split("_"))[timestamp_index]))

		for frame_ix, pv_frame_name in enumerate(frame_list):
			pv_frame_path = os.path.join(self.video_directory, pv_frame_name)

			pv_frame_array = cv2.imread(pv_frame_path)
			pv_timestamp = int(((pv_frame_name[:-extension_length]).split("_"))[timestamp_index])

			if self.tsfirst is None:
				self.tsfirst = pv_timestamp

			pv_frame_decoded = av.VideoFrame.from_ndarray(pv_frame_array, format=PV_VIDEO_DECODE)

			for packet in self.stream_video.encode(pv_frame_decoded):
				packet.stream = self.stream_video
				packet.pts = pv_timestamp - self.tsfirst
				packet.dts = packet.pts
				packet.time_base = self.time_base

				self.container.mux(packet)

			if frame_ix % 500 == 0:
				print(f'Processed {frame_ix}')

		self.container.close()


if __name__ == '__main__':
	add_to_sys_path()
	recording_instance = Recording("Coffee", "PL1", "P1", "R1", False)
	data_parent_directory = "/mnt/c/Users/rohit/PycharmProjects/data"
	recording_instance.set_device_ip('192.168.0.117')

	video_joiner = VideoJoiner(data_parent_directory, recording_instance)
	video_joiner.join_video()
