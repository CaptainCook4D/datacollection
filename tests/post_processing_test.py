import os
import shutil
import time

from concurrent.futures import ThreadPoolExecutor
from datacollection.user_app.backend.app.models.recording import Recording
from datacollection.user_app.backend.app.post_processing.compress_data_service import CompressDataService
from datacollection.user_app.backend.app.post_processing.nas_unzipping_service import multithreading_unzip
from datacollection.user_app.backend.app.services.box_service import BoxService
from datacollection.user_app.backend.app.services.firebase_service import FirebaseService
from datacollection.user_app.backend.app.services.synchronization_service import SynchronizationServiceV2
from datacollection.user_app.backend.app.utils.constants import Synchronization_Constants as const
from datacollection.user_app.backend.app.utils.logger_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def process_directory(
		data_parent_directory,
		data_recording_directory_name,
		db_service,
		box_service,
		temp_local_data_directory
):
	data_recording_directory_path = os.path.join(data_parent_directory, data_recording_directory_name)
	if os.path.isdir(data_recording_directory_path):
		recording = Recording.from_dict(db_service.fetch_recording(data_recording_directory_name))
		logger.info(f"[{recording.id}] BEGIN SYNCHRONIZATION")
		synchronization_service = SynchronizationServiceV2(
			data_parent_directory,
			recording,
			const.BASE_STREAM,
			const.SYNCHRONIZATION_STREAMS
		)
		synchronization_service.sync_streams()
		
		recording_id = recording.id
		
		remote_sync_data_directory = os.path.join(data_recording_directory_path, recording.id, const.SYNC)
		local_sync_data_directory = os.path.join(temp_local_data_directory, recording.id, const.SYNC)
		if not os.path.exists(local_sync_data_directory):
			os.makedirs(local_sync_data_directory)
		
		start_nas_to_local_time = time.time()
		logger.info(f"[{recording.id}] BEGIN NAS TO LOCAL")
		shutil.copytree(remote_sync_data_directory, local_sync_data_directory)
		total_nas_to_local_time = time.strftime(
			"%H:%M:%S",
			time.gmtime(time.time() - start_nas_to_local_time)
		)
		logger.info(f"[{recording.id}] END NAS TO LOCAL : {total_nas_to_local_time}")
		
		# ------------------ ZIPPING DEPTH FRAMES ------------------
		
		local_sync_depth_parent_directory = os.path.join(local_sync_data_directory, const.DEPTH_AHAT)
		
		local_sync_depth_frames_zip_file_path = os.path.join(local_sync_depth_parent_directory, const.DEPTH_ZIP)
		if not os.path.exists(local_sync_depth_frames_zip_file_path):
			logger.info(f"[{recording_id}] Compressing Depth data")
			start_compress_depth_time = time.time()
			CompressDataService.compress_dir(local_sync_depth_parent_directory, const.DEPTH)
			total_compress_depth_time = time.strftime(
				"%H:%M:%S",
				time.gmtime(time.time() - start_compress_depth_time)
			)
			logger.info(f"[{recording_id}] Done compressing Depth data : {total_compress_depth_time}")
		else:
			logger.info(f"[{recording_id}] Skipping compressing Depth data")
		
		sync_depth_ab_frames_zip_file_path = os.path.join(local_sync_depth_parent_directory, const.AB_ZIP)
		if not os.path.exists(sync_depth_ab_frames_zip_file_path):
			logger.info(f"[{recording_id}] Compressing Active Brightness data")
			start_compress_ab_time = time.time()
			CompressDataService.compress_dir(local_sync_depth_parent_directory, const.AB)
			total_compress_ab_time = time.strftime(
				"%H:%M:%S",
				time.gmtime(time.time() - start_compress_ab_time)
			)
			logger.info(f"[{recording_id}] Done compressing Active Brightness data : {total_compress_ab_time}")
		else:
			logger.info(f"[{recording_id}] Skipping compressing Active Brightness data")
		
		# ------------------ ZIPPING PV FRAMES ------------------
		
		local_sync_base_stream_directory = os.path.join(local_sync_data_directory, const.BASE_STREAM)
		sync_pv_frames_zip_file_path = os.path.join(local_sync_base_stream_directory, const.FRAMES_ZIP)
		if not os.path.exists(sync_pv_frames_zip_file_path):
			logger.info(f"[{recording_id}] Compressing pv frames directory")
			start_compress_pv_time = time.time()
			CompressDataService.compress_dir(local_sync_base_stream_directory, const.FRAMES)
			total_compress_pv_time = time.strftime(
				"%H:%M:%S",
				time.gmtime(time.time() - start_compress_pv_time)
			)
			logger.info(f"[{recording_id}] Done compressing pv frames directory : {total_compress_pv_time}")
		else:
			logger.info(f"[{recording_id}] Skipping compressing pv frames directory")
		
		logger.info(f"[{recording.id}] BEGIN UPLOADING TO BOX")
		box_service.upload_from_nas(recording, temp_local_data_directory)
		logger.info(f"[{recording.id}] END UPLOADING TO BOX")
		logger.info(f"[{recording.id}] END SYNCHRONIZATION")


def begin_post_processing():
	data_parent_directory = "/run/user/12345/gvfs/sftp:host=10.176.140.2/NetBackup/PTG"
	temp_local_data_directory = "/data/PTG"
	
	db_service = FirebaseService()
	box_service = BoxService()
	max_workers = 1
	data_recording_directories = os.listdir(data_parent_directory)
	logger.info("Preparing to synchronize using ThreadPoolExecutor with max_workers = 1")
	# Create a ThreadPoolExecutor with a suitable number of threads (e.g., 4)
	with ThreadPoolExecutor(max_workers=max_workers) as executor:
		for data_recording_directory_name in data_recording_directories:
			executor.submit(
				process_directory,
				data_parent_directory,
				data_recording_directory_name,
				db_service,
				box_service,
				temp_local_data_directory
			)


def begin_unzipping():
	data_parent_directory = "/run/user/12345/gvfs/sftp:host=10.176.140.2/NetBackup/PTG"
	db_service = FirebaseService()
	recording_list = []
	for data_recording_directory_name in os.listdir(data_parent_directory):
		data_recording_directory_path = os.path.join(data_parent_directory, data_recording_directory_name)
		if os.path.isdir(data_recording_directory_path):
			recording = Recording.from_dict(db_service.fetch_recording(data_recording_directory_name))
			recording_list.append(recording)
	recording_list.sort(key=lambda x: x.id)
	multithreading_unzip(recording_list, data_parent_directory)


if __name__ == '__main__':
	begin_post_processing()
# begin_unzipping()
