import concurrent
import json
import os
import time

from boxsdk import Client, CCGAuth

from ..models.annotation import Annotation
from ..models.activity import Activity
from ..services.firebase_service import FirebaseService
from ..models.recording import Recording
from ..utils.constants import Box_Constants as const
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


# Folder structure in BOX
# - Activity
# - <Recording_ID>
# 	- Raw
# 		- Depth Ahat
# 			- Ab
# 			- Depth
# 			- Pose
# 		- PV
# 			- Frames
# 			- Pose
# 		- Microphone
# 		- Spatial
# 	- Synchronized
# 		- Depth Ahat
# 			- Ab
# 			- Depth
# 			- Pose
# 		- PV
# 			- Frames
# 			- Pose
# 		- Spatial
# 	- GoPro
# 		- GoPro.mp4
# 	    - 360p
# 	- Pretrained Features
# 	- Annotations


class BoxService:
	
	def __init__(self):

		
		ccg_auth = CCGAuth(client_id=self.client_id, client_secret=self.client_secret, user=self.user_id)
		self.client = Client(ccg_auth)
		
		self.db_service = FirebaseService()
		self.activities = [
			Activity.from_dict(activity_dict)
			for activity_dict in self.db_service.fetch_activities()
			if activity_dict is not None
		]
		self._create_activity_id_name_map()
	
	def _create_activity_id_name_map(self):
		self.activity_id_name_map = {}
		for activity in self.activities:
			self.activity_id_name_map[activity.id] = activity.name
	
	def _fetch_folder_id(self, folder_name: str, parent_folder_id: str) -> (bool, str):
		folders = self.client.folder(folder_id=parent_folder_id).get_items(limit=1000)
		for folder in folders:
			if folder.name == folder_name:
				return True, folder.object_id
		return False, None
	
	def _fetch_activity_folder(self, activity_name):
		is_activity_present, activity_folder_id = self._fetch_folder_id(activity_name, self.root_folder_id)
		if not is_activity_present:
			activity_folder_id = (
				self.client.folder(folder_id=self.root_folder_id).create_subfolder(activity_name)).object_id
		return activity_folder_id
	
	def _fetch_subfolder(self, parent_folder_id, subfolder_name):
		is_subfolder_present, subfolder_id = self._fetch_folder_id(subfolder_name, parent_folder_id)
		if not is_subfolder_present:
			subfolder_id = (
				self.client.folder(folder_id=parent_folder_id).create_subfolder(subfolder_name)).object_id
		return subfolder_id
	
	def _upload_files_in_path(self, box_folder_id, folder_path, recording_id):
		box_folder = self.client.folder(folder_id=box_folder_id)
		box_files = {item for item in box_folder.get_items(limit=1000)}
		for file_name in os.listdir(folder_path):
			if not file_name.endswith(".zip") \
					and not file_name.endswith(".pkl") \
					and not file_name.endswith(".MP4") \
					and not file_name.endswith(".mp4"):
				logger.info(f"[{recording_id}] Skipping file: {file_name}")
				continue
			is_item_present = False
			local_file_size = os.path.getsize(os.path.join(folder_path, file_name))
			for box_item in box_files:
				if file_name == box_item.name:
					box_file_size = box_item.get().size
					if local_file_size == box_file_size:
						is_item_present = True
						logger.info(f"[{recording_id}] File already present: {file_name}")
					else:
						logger.info(f"[{recording_id}] Deleting file as the file size does not match: {file_name}")
						box_item.delete()
						is_item_present = False
			if not is_item_present:
				file_path = os.path.join(folder_path, file_name)
				logger.info(f"[{recording_id}] Uploading file: {file_name}")
				box_folder.upload(file_path)
				logger.info(f"[{recording_id}] Uploaded file: {file_name}")
	
	def _upload_folders_and_subfolders(self, parent_box_folder_id, parent_local_folder, folders, recording_id):
		for folder in folders:
			box_folder_id = self._fetch_subfolder(parent_box_folder_id, folder)
			local_folder_path = os.path.join(parent_local_folder, folder)
			self._upload_files_in_path(box_folder_id, local_folder_path, recording_id)
	
	def upload_from_nas(self, recording, data_parent_directory):
		activity_folder_id = self._fetch_activity_folder(self.activity_id_name_map[recording.activity_id])
		recording_folder_id = self._fetch_subfolder(activity_folder_id, recording.id)
		recording_id = recording.id
		data_recording_directory = os.path.join(data_parent_directory, recording.id)
		# raw_data_directory = os.path.join(data_recording_directory, const.RAW)
		# if os.path.exists(raw_data_directory):
		# 	logger.info(f"[{recording_id}] Uploading raw data")
		# 	raw_folder_id = self._fetch_subfolder(recording_folder_id, const.RAW)
		# 	self._upload_folders_and_subfolders(
		# 		raw_folder_id,
		# 		raw_data_directory,
		# 		[const.PV, const.DEPTH_AHAT, const.MICROPHONE, const.SPATIAL, const.IMU],
		# 		recording_id
		# 	)
		# 	logger.info(f"[{recording_id}] Raw data uploaded")

		sync_data_directory = os.path.join(data_recording_directory, const.SYNC)
		if os.path.exists(sync_data_directory):
			logger.info(f"[{recording_id}] Uploading synchronized data")
			sync_folder_id = self._fetch_subfolder(recording_folder_id, const.SYNC)
			self._upload_folders_and_subfolders(
				sync_folder_id,
				sync_data_directory,
				[const.PV, const.DEPTH_AHAT, const.SPATIAL, const.IMU]
			)
			logger.info(f"[{recording_id}] Synchronized data uploaded")
		
		# logger.info(f"[{recording_id}] Uploading gopro data")
		# gopro_folder_id = self._fetch_subfolder(recording_folder_id, const.GOPRO)
		# local_gopro_path = os.path.join(data_recording_directory, const.GOPRO)
		# self._upload_files_in_path(gopro_folder_id, local_gopro_path, recording_id)
		# logger.info(f"[{recording_id}] Gopro data uploaded")
	
	def upload_go_pro_360_video(self, recording, file_path):
		logger.info(f'Uploading GoPro 360 video for recording {recording.id}')
		activity_folder_id = self._fetch_activity_folder(self.activity_id_name_map[recording.activity_id])
		recording_folder_id = self._fetch_subfolder(activity_folder_id, recording.id)
		gopro_folder_id = self._fetch_subfolder(recording_folder_id, const.GOPRO)
		self.client.folder(folder_id=gopro_folder_id).upload(file_path)
		logger.info(f'Uploaded GoPro 360 video for recording {recording.id}')
	
	def upload_pretrained_features(self, recording, file_path):
		activity_folder_id = self._fetch_activity_folder(self.activity_id_name_map[recording.activity_id])
		recording_folder_id = self._fetch_subfolder(activity_folder_id, recording.id)
		pretrained_feature_folder_id = self._fetch_subfolder(recording_folder_id, const.PRETRAINED_FEATURES)
		self.client.folder(folder_id=pretrained_feature_folder_id).upload(file_path)
	
	def fetch_latest_annotation_json(self, recording_id, file_path):
		activity_id = recording_id.split('_')[0]
		activity_folder_id = self._fetch_activity_folder(self.activity_id_name_map[int(activity_id)])
		recording_folder_id = self._fetch_subfolder(activity_folder_id, recording_id)
		annotations_folder_id = self._fetch_subfolder(recording_folder_id, const.ANNOTATIONS)
		annotation_folders = self.client.folder(folder_id=annotations_folder_id).get_items()
		
		latest_annotation_folder_id = None
		# TODO: Check created timestamp and take the latest one only
		for annotation_folder in annotation_folders:
			latest_annotation_folder_id = annotation_folder.id
			break
		
		if latest_annotation_folder_id is None:
			return None
		
		# annotation_folders = sorted(annotation_folders, key=lambda x: x.created_at, reverse=True)
		
		# Fetch annotation json with file name recording_id + "_360p".json
		annotation_files = self.client.folder(folder_id=latest_annotation_folder_id).get_items()
		annotation_files = [file for file in annotation_files]
		with open(os.path.join(file_path), 'wb') as annotation_json_file:
			self.client.file(file_id=annotation_files[0].id).download_to(annotation_json_file)
		with open(os.path.join(file_path), 'r') as annotation_json_file:
			annotation_json = json.load(annotation_json_file)
		
		return annotation_json
	
	def upload_annotation(self, annotation: Annotation, backup_annotation_file_path):
		recording_id = annotation.recording_id
		activity_id = recording_id.split('_')[0]
		activity_folder_id = self._fetch_activity_folder(self.activity_id_name_map[int(activity_id)])
		recording_folder_id = self._fetch_subfolder(activity_folder_id, recording_id)
		annotations_folder_id = self._fetch_subfolder(recording_folder_id, const.ANNOTATIONS)
		current_timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
		timed_annotation_folder_id = self._fetch_subfolder(annotations_folder_id, f"{current_timestamp}")
		self.client.folder(folder_id=timed_annotation_folder_id).upload(backup_annotation_file_path)
	
	def upload_in_threads(self, recordings, data_parent_directory, max_workers=5):
		with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
			futures = {
				executor.submit(self.upload_from_nas, recording, data_parent_directory): recording
				for recording in recordings
			}
			for future in concurrent.futures.as_completed(futures):
				recording = futures[future]
				try:
					future.result()
				except Exception as exc:
					logger.error('%r generated an exception: %s' % (recording, exc))


if __name__ == '__main__':
	box_service = BoxService()
