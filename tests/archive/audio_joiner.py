import os
import sys

import logging

import pickle
import wave

import av

from fractions import Fraction

import pyaudio

from datacollection.backend.Recording import Recording
from datacollection.backend.constants import *

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


class AudioJoiner:
	
	def __init__(self, data_directory, recording):
		
		self.tsfirst = None
		self.recording = recording
		self.time_base = Fraction(1, hl2ss.TimeBase.HUNDREDS_OF_NANOSECONDS)
		
		self.recording_id = self.recording.get_recording_id()
		self.data_directory = os.path.join(data_directory, self.recording_id)
		
		self.audio_file_name = f'{self.recording_id}_mc.pkl'
		self.audio_directory = os.path.join(self.data_directory, "mc")
		self.audio_file_path = os.path.join(self.audio_directory, self.audio_file_name)
		
		self.processed_audio_name = f'{self.recording_id}_audio.mp4'
	
	def join_encoded_audio_from_pkl(self, audio_profile, sample_rate, start_timestamp=None, end_timestamp=None):
		
		codec_audio = av.CodecContext.create(hl2ss.get_audio_codec_name(audio_profile), 'r')
		
		is_partial = False
		container = av.open(self.processed_audio_name, 'w')
		stream_audio = container.add_stream(hl2ss.get_audio_codec_name(audio_profile), rate=sample_rate)
		
		if start_timestamp is not None and end_timestamp is not None:
			self.processed_audio_name = f'{self.recording_id}_{start_timestamp}_{end_timestamp}.mp4'
			is_partial = True
		
		with open(self.audio_file_path, 'rb') as mc_file:
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
						container.mux(packet)
				except EOFError:
					break
		container.close()
	
	def join_raw_audio(self, start_timestamp=None, end_timestamp=None):
		
		wave_output_file_name = f'{self.recording_id}_audio.wav'
		
		p = pyaudio.PyAudio()

		with open(self.audio_file_path, 'rb') as mc_file:
			mc_chunk = mc_file.read()

		wave_file = wave.open(wave_output_file_name, 'wb')
		wave_file.setnchannels(hl2ss.Parameters_MICROPHONE.CHANNELS)
		wave_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
		wave_file.setframerate(hl2ss.Parameters_MICROPHONE.SAMPLE_RATE)
		wave_file.writeframes(mc_chunk)
		wave_file.close()


if __name__ == '__main__':
	add_to_sys_path()
	
	recording_instance = Recording("Coffee", "PL1", "P1", "R4", False)
	data_parent_directory = "/mnt/c/Users/rohit/PycharmProjects/data"
	recording_instance.set_device_ip('192.168.0.117')
	
	audio_joiner = AudioJoiner(data_parent_directory, recording_instance)
	audio_joiner.join_encoded_audio_from_pkl(AUDIO_PROFILE_DECODED, hl2ss.Parameters_MICROPHONE.SAMPLE_RATE)
# audio_joiner.join_audio()
# audio_joiner.save_multiple(199583000000, 199588000000)
