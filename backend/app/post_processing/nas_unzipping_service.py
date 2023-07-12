import concurrent
import os
import time
import zipfile

import cv2

from ..models.recording import Recording
from ..utils.constants import Synchronization_Constants as const
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


def create_directories(dir_path):
	if not os.path.exists(dir_path):
		os.makedirs(dir_path)


def extract_zip_file(zip_file_path, output_directory, recording_id):
	logger.info(f"[{recording_id}] Extracting zip file: {zip_file_path}")
	start_time = time.time()
	with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
		zip_ref.extractall(output_directory)
	extraction_time = time.time() - start_time
	extraction_time_readable = time.strftime("%H:%M:%S", time.gmtime(extraction_time))
	logger.info(f"[{recording_id}] Extracting zip file took: {extraction_time_readable}")


def make_video(images_folder, video_name, recording_id):
	images = [img for img in os.listdir(images_folder) if img.endswith(".jpg")]
	images = sorted(images, key=lambda x: int((x[:-4].split("_"))[-1]))
	
	frame = cv2.imread(os.path.join(images_folder, images[0]))
	height, width, layers = frame.shape
	
	fourcc = cv2.VideoWriter_fourcc(*'mp4v')
	# video = cv2.VideoWriter(video_name, 0, 30, (width, height))
	video = cv2.VideoWriter(video_name, fourcc, 30, (width, height))
	
	start_time = time.time()
	for image in images:
		video.write(cv2.imread(os.path.join(images_folder, image)))
	
	cv2.destroyAllWindows()
	video.release()
	
	video_creation_time = time.time() - start_time
	video_creation_time_readable = time.strftime("%H:%M:%S", time.gmtime(video_creation_time))
	logger.info(f"[{recording_id}] Video creation took: {video_creation_time_readable}")


def unzip_recording_data(recording: Recording, data_parent_directory: str):
	logger.info(f"[{recording.get_recording_id()}] Begin unzipping recording data")
	recording = recording
	recording_id = recording.get_recording_id()
	data_recording_directory = os.path.join(data_parent_directory, recording_id)
	
	raw_data_directory = os.path.join(data_recording_directory, const.RAW)
	sync_data_directory = os.path.join(data_recording_directory, const.SYNC)

	if not os.path.exists(raw_data_directory):
		logger.info(f"[{recording_id}] Raw data directory does not exist, no unzipping required")
		return
	
	raw_base_stream_directory = os.path.join(raw_data_directory, const.PHOTOVIDEO)
	sync_base_stream_directory = os.path.join(sync_data_directory, const.PHOTOVIDEO)
	create_directories(sync_base_stream_directory)
	
	# ------------------ Base stream ------------------
	# 1. Create base stream keys used to synchronize the rest of the data
	frames_zip_file_path = os.path.join(raw_base_stream_directory, const.FRAMES_ZIP)
	raw_base_stream_frames_dir = os.path.join(raw_base_stream_directory, const.FRAMES)
	if os.path.exists(frames_zip_file_path) and not os.path.exists(raw_base_stream_frames_dir):
		logger.info(f"[{recording_id}] Extracting pv frames")
		extract_zip_file(frames_zip_file_path, raw_base_stream_frames_dir, recording_id)
		logger.info(f"[{recording_id}] Done extracting pv frames")
	
	recording_base_stream_mp4_file_path = os.path.join(sync_base_stream_directory, f"{recording.id}.mp4")
	if not os.path.exists(recording_base_stream_mp4_file_path):
		logger.info(f"[{recording_id}] Recording base stream mp4 file does not exist")
		logger.info(f"[{recording_id}] Creating recording base stream mp4 file")
		make_video(raw_base_stream_frames_dir, recording_base_stream_mp4_file_path, recording_id)
		logger.info(f"[{recording_id}] Done creating recording base stream mp4 file")
	
	# ------------------ Depth ------------------
	# Files and directories
	raw_depth_parent_directory = os.path.join(raw_data_directory, const.DEPTH_AHAT)
	
	raw_depth_data_directory = os.path.join(raw_depth_parent_directory, const.DEPTH)
	depth_frames_zip_file_path = os.path.join(raw_depth_parent_directory, const.DEPTH_ZIP)
	if os.path.exists(depth_frames_zip_file_path) and not os.path.exists(raw_depth_data_directory):
		logger.info(f"[{recording_id}] Extracting depth frames zip file")
		extract_zip_file(depth_frames_zip_file_path, raw_depth_data_directory, recording_id)
		logger.info(f"[{recording_id}] Done extracting depth frames zip file")
	
	raw_depth_ab_directory = os.path.join(raw_depth_parent_directory, const.AB)
	ab_frames_zip_file_path = os.path.join(raw_depth_parent_directory, const.AB_ZIP)
	if os.path.exists(depth_frames_zip_file_path) and not os.path.exists(raw_depth_ab_directory):
		logger.info(f"[{recording_id}] Extracting ab frames zip file")
		extract_zip_file(ab_frames_zip_file_path, raw_depth_ab_directory, recording_id)
		logger.info(f"[{recording_id}] Done extracting ab frames zip file")
		
	logger.info(f"[{recording_id}] Finished unzipping recording data")


def multithreading_unzip(recordings, data_parent_directory, max_workers=10):
	with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
		futures = {
			executor.submit(unzip_recording_data, recording, data_parent_directory): recording
			for recording in recordings
		}
		for future in concurrent.futures.as_completed(futures):
			recording = futures[future]
			try:
				future.result()
			except Exception as exc:
				logger.error('%r generated an exception: %s' % (recording, exc))
