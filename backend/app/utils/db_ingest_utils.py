import os
import yaml

from ..models.annotation_assignment import AnnotationAssignment
from ..models.environment import Environment
from ..services.firebase_service import FirebaseService
from ..models.activity import Activity
from ..models.recording import Recording
from ..models.recording_ingestion_helper import RecordingIngestionHelper
from ..models.user import User
from .constants import DatabaseIngestion_Constants as const

from .logger_config import get_logger

logger = get_logger(__name__)


class FirebaseIngestion:
	
	def __init__(self, data_directory, remove_past_data=False):
		self.db_service = FirebaseService()
		self.data_directory = data_directory
		self.remove_past_data = remove_past_data
	
	def ingest(self):
		pass


class UserIngestion(FirebaseIngestion):
	
	def __init__(self, data_directory, remove_past_data=False):
		super().__init__(data_directory, remove_past_data)
	
	def ingest(self):
		if self.remove_past_data:
			self.db_service.remove_all_users()
		
		users_yaml_file_path = os.path.join(self.data_directory, const.USERS_YAML_FILE_NAME)
		with open(users_yaml_file_path, 'r') as users_yaml_file:
			users_data = yaml.safe_load(users_yaml_file)
		
		for user_data in users_data:
			user = User.from_dict(user_data)
			self.db_service.update_user(user)


class ActivitiesIngestion(FirebaseIngestion):
	
	def __init__(self, data_directory, remove_past_data=False):
		super().__init__(data_directory, remove_past_data)
	
	def ingest(self):
		if self.remove_past_data:
			self.db_service.remove_all_activities()
		
		activities_yaml_file_path = os.path.join(self.data_directory, const.ACTIVITIES_YAML_FILE_NAME)
		with open(activities_yaml_file_path, 'r') as activities_yaml_file:
			activities_data = yaml.safe_load(activities_yaml_file)
		
		for activity_data in activities_data:
			activity = Activity.from_yaml_dict(activity_data)
			self.db_service.update_activity(activity)


class ActivityRecordingsIngestion(FirebaseIngestion):
	
	def __init__(self, data_directory, remove_past_data=False):
		super().__init__(data_directory, remove_past_data)
		self.recordings_directory = os.path.join(self.data_directory, const.RECORDINGS)
	
	def ingest(self):
		if self.remove_past_data:
			self.db_service.remove_all_recordings()
		
		activities = self.db_service.fetch_activities()
		
		def fetch_activity(name):
			for _activity in activities:
				if _activity is None:
					continue
				processed_activity_name = (_activity[const.NAME].lower()).replace(" ", "")
				if name in processed_activity_name:
					return _activity
			return None
		
		for activity_recordings_file_name in os.listdir(self.recordings_directory):
			logger.info("----------------------------------------")
			logger.info(f'Processing activity recordings file: {activity_recordings_file_name}')
			
			activity_name = activity_recordings_file_name
			activity_dict = fetch_activity(activity_name[:-5])
			activity = Activity.from_dict(activity_dict)
			
			activity_recordings_yaml_file_path = os.path.join(self.recordings_directory, activity_recordings_file_name)
			with open(activity_recordings_yaml_file_path, 'r') as activity_recordings_yaml_file:
				activity_recordings_data = yaml.safe_load(activity_recordings_yaml_file)
			
			for activity_recording in activity_recordings_data:
				recording_helper = RecordingIngestionHelper.from_dict(activity_recording)
				
				# 1. Create Recording instance from the given data
				processed_recording_id = f'{activity.id}_{recording_helper.recording_id}'
				is_error = False
				errors = None
				if recording_helper.errors is not None:
					errors = recording_helper.errors
					is_error = len(recording_helper.errors) > 0
				
				recording = Recording(
					id=processed_recording_id,
					activity_id=activity.id,
					is_error=is_error,
					steps=recording_helper.steps,
					errors=errors
				)
				
				# 2. Push it to the database as a child of activity with corresponding activity_id
				self.db_service.update_recording(recording)
			
			logger.info("----------------------------------------")
			
			
class EnvironmentIngestion(FirebaseIngestion):
	
	def __init__(self, data_directory, remove_past_data=False):
		super().__init__(data_directory, remove_past_data)
	
	def ingest(self):
		if self.remove_past_data:
			self.db_service.remove_all_environments()
		
		environments_yaml_file_path = os.path.join(self.data_directory, const.ENVIRONMENTS_YAML_FILE_NAME)
		with open(environments_yaml_file_path, 'r') as environments_yaml_file:
			environments_data = yaml.safe_load(environments_yaml_file)
		
		for environment_data in environments_data:
			environment = Environment.from_dict(environment_data)
			self.db_service.update_environment(environment)


class AnnotationAssignmentIngestion(FirebaseIngestion):
	
	def __init__(self, data_directory, remove_past_data=False):
		super().__init__(data_directory, remove_past_data)
	
	def ingest(self):
		if self.remove_past_data:
			self.db_service.remove_all_annotation_assignments()
		
		annotation_assignment_yaml_file_path = os.path.join(self.data_directory, const.ANNOTATION_ASSIGNMENT_YAML_FILE_NAME)
		with open(annotation_assignment_yaml_file_path, 'r') as annotations_yaml_file:
			annotation_assignment_data = yaml.safe_load(annotations_yaml_file)
		
		for annotation_assignment_data in annotation_assignment_data:
			annotation_assignment = AnnotationAssignment.from_dict(annotation_assignment_data)
			self.db_service.update_annotation_assignment(annotation_assignment)
