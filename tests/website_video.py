import os

import cv2
import numpy as np
from moviepy.editor import VideoFileClip, clips_array
from moviepy.video.VideoClip import ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

DEFAULT_MARGIN = 0
DIFFERENCE_MARGIN = 50


def combine_videos(videos, output_path):
	combined_clip = clips_array(videos)
	clip_size = combined_clip.size
	pos = 'center'

	white_clip = ColorClip(clip_size, color=np.array([215, 215, 215])).set_duration(combined_clip.duration)
	
	final_clip = CompositeVideoClip([white_clip, combined_clip.set_position(pos)], use_bgclip=True, bg_color=None)
	final_clip.write_videofile(output_path, fps=30)


def combine_category_videos(category_videos, output_path, error_category_name):
	"""Combine category videos into one video

	Args:
		category_videos (list): List of category videos
		output_path (str): Path to output video
	"""
	normal_video_1 = VideoFileClip(category_videos[0]).subclip(0, 5).margin(DEFAULT_MARGIN)
	normal_video_2 = VideoFileClip(category_videos[1]).subclip(0, 5).margin(DEFAULT_MARGIN)
	
	normal_video_output_path = os.path.join(os.path.dirname(output_path), f"{error_category_name}_normal.mp4")
	combine_videos([[normal_video_1, normal_video_2]], normal_video_output_path)
	
	error_video_1 = VideoFileClip(category_videos[2]).subclip(0, 5).margin(DEFAULT_MARGIN)
	error_video_2 = VideoFileClip(category_videos[3]).subclip(0, 5).margin(DEFAULT_MARGIN)
	error_video_3 = VideoFileClip(category_videos[4]).subclip(0, 5).margin(DEFAULT_MARGIN)
	
	error_video_output_path = os.path.join(os.path.dirname(output_path), f"{error_category_name}_error.mp4")
	combine_videos([[error_video_1, error_video_2, error_video_3]], error_video_output_path)
	
	normal_video = VideoFileClip(normal_video_output_path).subclip(0, 5).margin(DIFFERENCE_MARGIN)
	error_video = VideoFileClip(error_video_output_path).subclip(0, 5).margin(DIFFERENCE_MARGIN)
	
	combine_videos([[normal_video, error_video]], output_path)


def combine_categories(categories, output_path):
	error_categories = []
	for category in categories:
		error_category_clip = VideoFileClip(category).subclip(0, 5)
		error_categories.append([error_category_clip])
	
	final_clip = clips_array(error_categories)
	final_clip.write_videofile(output_path, fps=30)


def prepare_video():
	data_parent_directory = r"D:\DATA\COLLECTED\PTG\WEBSITE\ERROR_CATEGORIES"
	
	# 1. Technique Error
	te1_normal_video_1 = "13_14_360p.mp4"
	te1_normal_video_2 = "13_24_360p.mp4"
	
	te1_error_video_1 = "13_32_360p.mp4"
	te1_error_video_2 = "13_41_360p.mp4"
	te1_error_video_3 = "13_44_360p.mp4"
	
	te1_category_videos = [
		te1_normal_video_1, te1_normal_video_2, te1_error_video_1, te1_error_video_2, te1_error_video_3
	]
	te1_category_videos = [os.path.join(data_parent_directory, video) for video in te1_category_videos]
	te1_output_path = os.path.join(data_parent_directory, "technique_error_1.mp4")
	if not os.path.exists(te1_output_path):
		combine_category_videos(te1_category_videos, te1_output_path, "technique_error_1")
	
	# 2. Technique Error
	te2_normal_video_1 = "17_10_360p.mp4"
	te2_normal_video_2 = "17_11_360p.mp4"
	
	te2_error_video_1 = "17_29_360p.mp4"
	te2_error_video_2 = "17_45_360p.mp4"
	te2_error_video_3 = "17_49_360p.mp4"
	
	te2_category_videos = [
		te2_normal_video_1, te2_normal_video_2, te2_error_video_1, te2_error_video_2, te2_error_video_3
	]
	te2_category_videos = [os.path.join(data_parent_directory, video) for video in te2_category_videos]
	te2_output_path = os.path.join(data_parent_directory, "technique_error_2.mp4")
	if not os.path.exists(te2_output_path):
		combine_category_videos(te2_category_videos, te2_output_path, "technique_error_2")
	
	# 3. Measurement Error
	me_normal_video_1 = "16_10_360p.mp4"
	me_normal_video_2 = "16_18_360p.mp4"
	
	me_error_video_1 = "16_26_360p.mp4"
	me_error_video_2 = "16_27_360p.mp4"
	me_error_video_3 = "16_44_360p.mp4"
	
	me_category_videos = [
		me_normal_video_1, me_normal_video_2, me_error_video_1, me_error_video_2, me_error_video_3
	]
	me_category_videos = [os.path.join(data_parent_directory, video) for video in me_category_videos]
	me_output_path = os.path.join(data_parent_directory, "measurement_error.mp4")
	if not os.path.exists(me_output_path):
		combine_category_videos(me_category_videos, me_output_path, "measurement_error")
	
	# 4. Preparation Error
	pe_normal_video_1 = "26_4_360p.mp4"
	pe_normal_video_2 = "26_17_360p.mp4"
	
	pe_error_video_1 = "26_30_360p.mp4"
	pe_error_video_2 = "26_36_360p.mp4"
	pe_error_video_3 = "26_39_360p.mp4"
	
	pe_category_videos = [
		pe_normal_video_1, pe_normal_video_2, pe_error_video_1, pe_error_video_2, pe_error_video_3
	]
	pe_category_videos = [os.path.join(data_parent_directory, video) for video in pe_category_videos]
	pe_output_path = os.path.join(data_parent_directory, "preparation_error.mp4")
	if not os.path.exists(pe_output_path):
		combine_category_videos(pe_category_videos, pe_output_path, "preparation_error")
	
	# 5. Order Error
	oe_normal_video_1 = "28_10_360p.mp4"
	oe_normal_video_2 = "28_21_360p.mp4"
	
	oe_error_video_1 = "28_38_360p.mp4"
	oe_error_video_2 = "28_45_360p.mp4"
	oe_error_video_3 = "28_50_360p.mp4"
	
	oe_category_videos = [
		oe_normal_video_1, oe_normal_video_2, oe_error_video_1, oe_error_video_2, oe_error_video_3
	]
	oe_category_videos = [os.path.join(data_parent_directory, video) for video in oe_category_videos]
	oe_output_path = os.path.join(data_parent_directory, "order_error.mp4")
	if not os.path.exists(oe_output_path):
		combine_category_videos(oe_category_videos, oe_output_path, "order_error")
	
	final_path = os.path.join(data_parent_directory, "error_categories.mp4")
	
	if not os.path.exists(final_path):
		combine_categories(
			[te1_output_path, te2_output_path, me_output_path, pe_output_path, oe_output_path],
			final_path
		)
	
	return final_path


def insert_text_in_video(input_video_path, output_video_path):
	video_capture = cv2.VideoCapture(input_video_path)
	
	# Get the frames per second (fps) of the video
	fps = video_capture.get(cv2.CAP_PROP_FPS)
	
	# Get the codec information of the video
	fourcc = cv2.VideoWriter_fourcc(*'mp4v')
	
	# Get the width and height of the frames in the video
	frame_width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
	frame_height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
	
	# Create a VideoWriter object
	out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))
	
	while True:
		# Capture frames in the video
		ret, frame = video_capture.read()
		
		if ret:
			# Describe the type of font
			# to be used.
			font = cv2.FONT_HERSHEY_SIMPLEX
			
			# Use putText() method for
			# inserting text on video
			cv2.putText(frame, 'TEXT ON VIDEO', (50, 50), font, 1, (0, 255, 255), 2, cv2.LINE_4)
			
			# Write the frame into the file 'output.mp4'
			out.write(frame)
		
		# # Display the resulting frame
		# cv2.imshow('video', frame)
		else:
			break
		
		# Creating 'q' as the quit
		# button for the video
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
	
	# Release the cap and out objects
	video_capture.release()
	out.release()
	
	# Close all windows
	cv2.destroyAllWindows()


if __name__ == "__main__":
	video_output_path = prepare_video()
# insert_text_in_video(video_output_path, video_output_path[:-4] + "_modified.mp4")
