import os
import yaml

from datacollection.user_app.backend.app.models.activity import Activity
from datacollection.user_app.backend.app.models.recording import Recording
from datacollection.user_app.backend.app.services.firebase_service import FirebaseService


def create_directories(dir_path):
	if not os.path.exists(dir_path):
		os.makedirs(dir_path)


class PanRecipeUpdate:
	
	def __init__(self):
		self.db_versions_dir = ""
		self.current_version = 3
		self.db_service = FirebaseService()
	
	# self._create_new_version_db()
	# self._update_version_db(version=self.current_version)
	
	def _create_new_version_db(self):
		# 1. Download all the recording objects from the firebase which are nor yet recorded
		
		activity_list = self.db_service.fetch_activities()
		activities = [Activity.from_dict(activity) for activity in activity_list if activity is not None]
		
		db_version_path = f"../backend/info_files/db_versions/v_{self.current_version}"
		create_directories(db_version_path)
		for activity in activities:
			activity_version_path = os.path.join(db_version_path, f"{activity.name}.yaml")
			
			all_activity_recordings = self.db_service.fetch_all_activity_recordings(activity.id)
			
			unrecorded_activity_recordings = []
			for (recording_id, recording_dict) in all_activity_recordings.items():
				recording = Recording.from_dict(recording_dict)
				if recording.recorded_by == -1:
					unrecorded_activity_recordings.append(recording)
			
			sorted_unrecorded_activity_recordings = sorted(unrecorded_activity_recordings,
			                                               key=lambda x: int(x.id.split("_")[-1]))
			
			sorted_unrecorded_activity_recordings_dict_list = [recording.to_dict() for recording in
			                                                   sorted_unrecorded_activity_recordings]
			
			with open(activity_version_path, 'w') as yaml_file:
				yaml.dump(sorted_unrecorded_activity_recordings_dict_list, yaml_file)
	
	def _update_pan_db(self, version):
		
		# 1. Update the database files of all the recordings that are not updated yet
		activity_list = ["Pan Fried Tofu", "Zoodles", "Scrambled Eggs", "Blender Banana Pancakes",
		                 "Herb Omelet with Fried Tomatoes",
		                 "Tomato Chutney", "Broccoli Stir Fry", "Caprese Bruschetta", "Sauted Mushrooms"]
		
		if version is None:
			version = self.current_version
		
		db_version_path = f"../backend/info_files/db_versions/v_{version}"
		for activity in activity_list:
			activity_version_path = os.path.join(db_version_path, f"{activity}.yaml")
			with open(activity_version_path, 'r') as activity_recordings_yaml_file:
				activity_recordings_data = yaml.safe_load(activity_recordings_yaml_file)
			
			print(f"Updating activity recordings for activity: {activity}")
			for activity_recording in activity_recordings_data:
				recording = Recording.from_dict(activity_recording)
				print(f"Updating recording: {recording.id}")
				self.db_service.update_recording(recording)
				print(f"Recording: {recording.id} updated")
	
	def _update_activities_db(self, version):
		activity_list = self.db_service.fetch_activities()
		activities = [Activity.from_dict(activity) for activity in activity_list if activity is not None]
		
		if version is None:
			version = self.current_version
		
		db_version_path = f"../backend/info_files/db_versions/v_{version}"
		for activity in activities:
			activity_version_path = os.path.join(db_version_path, f"{activity.name}.yaml")
			with open(activity_version_path, 'r') as activity_recordings_yaml_file:
				activity_recordings_data = yaml.safe_load(activity_recordings_yaml_file)
			
			print(f"Updating activity recordings for activity: {activity}")
			for activity_recording in activity_recordings_data:
				recording = Recording.from_dict(activity_recording)
				print(f"Updating recording: {recording.id}")
				self.db_service.update_recording(recording)
				print(f"Recording: {recording.id} updated")
	
	def download_all_recorded_activities_from_db(self):
		# 1. Download all the recording objects from the firebase which are nor yet recorded
		
		activity_list = self.db_service.fetch_activities()
		activities = [Activity.from_dict(activity) for activity in activity_list if activity is not None]
		
		db_version_path = f"../backend/info_files/db_versions/v_{self.current_version}"
		create_directories(db_version_path)
		for activity in activities:
			activity_version_path = os.path.join(db_version_path, f"{activity.name}.yaml")
			
			all_activity_recordings = self.db_service.fetch_all_activity_recordings(activity.id)
			
			activity_recording_list = []
			for (recording_id, recording_dict) in all_activity_recordings.items():
				recording = Recording.from_dict(recording_dict)
				if recording.recorded_by != -1:
					activity_recording_list.append(recording)
			
			sorted_recorded_activity_recordings = sorted(activity_recording_list,
			                                               key=lambda x: int(x.id.split("_")[-1]))
			
			sorted_recorded_activity_recordings_dict_list = [recording.to_dict() for recording in
			                                                   sorted_recorded_activity_recordings]
			
			with open(activity_version_path, 'w') as yaml_file:
				yaml.dump(sorted_recorded_activity_recordings_dict_list, yaml_file)


if __name__ == '__main__':
	pan_recipe_update = PanRecipeUpdate()
	pan_recipe_update.download_all_recorded_activities_from_db()
