# import os
#
# import av
# import numpy as np
#
# from datacollection.backend.Recording import Recording
# from datacollection.backend.post_processing.audio_joiner import AudioJoiner
# from datacollection.backend.post_processing.audio_video_mux import AudioVideoMuxer
# from datacollection.backend.post_processing.video_joiner import VideoJoiner
# from datacollection.backend.constants import *
#
#
# class AudioVideoService:
#
# 	def __init__(self, data_parent_directory, recording: Recording):
# 		self.recording = recording
# 		self.data_parent_directory = data_parent_directory
#
# 		self.data_directory = os.path.join(self.data_parent_directory, self.recording.get_recording_id())
#
# 		self.audio_joiner = AudioJoiner(self.data_directory, self.recording)
# 		self.video_joiner = VideoJoiner(self.data_directory, self.recording)
# 		self.audio_video_muxer = AudioVideoMuxer(self.data_directory, self.recording)
#
# 	def change_resolution(self, output_width=640, output_height=360):
# 		# 1. Get the video file name
# 		input_video_name = f'{self.recording.get_recording_id()}.mp4'
# 		output_video_name = f'{self.recording.get_recording_id()}_{output_height}.mp4'
#
# 		# 2. Input video parameters
# 		input_video_path = os.path.join(self.data_directory, input_video_name)
# 		input_container = av.open(input_video_path)
#
# 		# 3. Output video parameters
# 		# TODO: Change it according to the required directory
# 		output_video_path = os.path.join(self.data_directory, output_video_name)
# 		output_container = av.open(output_video_path, mode='w')
#
# 		output_video = output_container.add_stream('h264', rate=input_container.streams.video[0].rate)
# 		output_video.width = output_width
# 		output_video.height = output_height
# 		output_video.pix_fmt = 'yuv420p'
#
# 		# 4. Loop through all the frames and resize each frame to match the output parameters
# 		for frame_packet in input_container.demux():
# 			for frame in frame_packet.decode():
# 				# Resize frame to 360p
# 				frame = np.array(frame.to_image().resize((output_width, output_height)))
# 				# Encode and write frame to output file
# 				out_packet = output_video.encode(frame)
# 				output_container.mux(out_packet)
#
# 		input_container.close()
# 		output_container.close()
#
# 	def generate_audio(self, audio_profile, sample_rate, start_timestamp=None, end_timestamp=None):
# 		if audio_profile == AUDIO_PROFILE_RAW:
# 			self.audio_joiner.join_raw_audio(start_timestamp, end_timestamp)
# 		elif audio_profile == AUDIO_PROFILE_DECODED:
# 			self.audio_joiner.join_encoded_audio_from_pkl(audio_profile, sample_rate, start_timestamp, end_timestamp)
#
# 	def generate_video(self):
# 		self.video_joiner.join_video()
#
# 	def generate_muxed_audio_video(self):
# 		pass
