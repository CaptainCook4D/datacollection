# This file contains all files related to firebase
import time

import pyrebase

from ..utils.constants import Firebase_Constants as const
from ..models.activity import Activity
from ..models.environment import Environment
from ..models.user_environment import UserEnvironment
from ..models.recording import Recording
from ..models.user import User
from ..utils.logger_config import get_logger

logger = get_logger(__name__)

firebase = None

logger.info("----------------------------------------------------------------------")
logger.info("Setting up Firebase Service...in " + const.DEPLOYMENT + " mode ")
logger.info("----------------------------------------------------------------------")


class FirebaseService:
	
	# 1. Have this db connection constant
	def __init__(self):
		self.db = firebase.database()
	
	# ---------------------- BEGIN ENVIRONMENT ----------------------
	def fetch_current_environment(self):
		return self.db.child(const.CURRENT_ENVIRONMENT).get().val()
	
	# ---------------------- END ENVIRONMENT ----------------------
	
	# ---------------------- BEGIN USER ----------------------
	def fetch_users(self):
		return self.db.child(const.USERS).get().val()
	
	def update_user(self, user: User):
		self.db.child(const.USERS).child(user.id).set(user.to_dict())
		logger.info(f"Updated user in the firebase - {user.__str__()}")
	
	def fetch_user(self, user_id: int):
		return self.db.child(const.USERS).child(user_id).get().val()
	
	def remove_all_users(self):
		self.db.child(const.USERS).remove()
	
	# ---------------------- END USER ----------------------
	
	# ---------------------- BEGIN ACTIVITY ----------------------
	
	def fetch_activities(self):
		return self.db.child(const.ACTIVITIES).get().val()
	
	def update_activity(self, activity: Activity):
		self.db.child(const.ACTIVITIES).child(activity.id).set(activity.to_dict())
		logger.info(f"Updated activity in the firebase - {activity.__str__()}")
	
	def remove_all_activities(self):
		self.db.child(const.ACTIVITIES).remove()
	
	# ---------------------- END ACTIVITY ----------------------
	
	# ---------------------- BEGIN RECORDING ----------------------
	
	def update_recording(self, recording: Recording):
		self.db.child(const.RECORDINGS).child(recording.id).set(recording.to_dict())
		logger.info(f"Updated recording in the firebase - {recording.__str__()}")
	
	def fetch_user_recordings(self, user_id):
		return self.db.child(const.RECORDINGS).order_by_child(const.RECORDED_BY).equal_to(user_id).get().val()
	
	def fetch_user_selections(self, user_id):
		return self.db.child(const.RECORDINGS).order_by_child(const.SELECTED_BY).equal_to(user_id).get().val()
	
	def fetch_all_selected_recordings(self):
		all_recordings = self.db.child(const.RECORDINGS).get()
		selected_recordings = {}
		for recording in all_recordings.each():
			if recording.val()[const.SELECTED_BY] != -1:
				selected_recordings[recording.key()] = recording.val()
		
		return selected_recordings
	
	def fetch_all_activity_recordings(self, activity_id):
		return self.db.child(const.RECORDINGS).order_by_child(const.ACTIVITY_ID).equal_to(activity_id).get().val()
	
	def fetch_recording(self, recording_id):
		return self.db.child(const.RECORDINGS).child(recording_id).get().val()
	
	def remove_all_recordings(self):
		self.db.child(const.RECORDINGS).remove()
	
	def fetch_environment_recordings(self, environment):
		return self.db.child(const.RECORDINGS).order_by_child(const.ENVIRONMENT).equal_to(environment).get().val()
	
	# ---------------------- END RECORDING ----------------------
	
	# ---------------------- BEGIN USER ENVIRONMENT ----------------------
	
	def update_environment(self, environment: Environment):
		self.db.child(const.ENVIRONMENTS).child(environment.get_id()).set(environment.to_dict())
		logger.info(f"Updated environment in the firebase - {environment.__str__()}")
	
	def fetch_environments(self):
		return self.db.child(const.ENVIRONMENTS).get().val()
	
	def remove_all_environments(self):
		self.db.child(const.ENVIRONMENTS).remove()
	
	# ---------------------- END USER ENVIRONMENT ----------------------
	
	# ---------------------- BEGIN ANNOTATIONS ----------------------
	def fetch_annotation_assignment(self):
		return self.db.child(const.ANNOTATION_ASSIGNMENTS).get().val()
	
	def update_annotation_assignment(self, annotation_assignment):
		self.db.child(const.ANNOTATION_ASSIGNMENTS).child(annotation_assignment.user_id).set(
			annotation_assignment.to_dict())
		logger.info(f"Updated annotation assignment in the firebase - {annotation_assignment.__str__()}")
	
	def remove_all_annotation_assignments(self):
		self.db.child(const.ANNOTATION_ASSIGNMENTS).remove()
	
	def fetch_user_annotation_assignment(self, user_id):
		return self.db.child(const.ANNOTATION_ASSIGNMENTS).child(user_id).get().val()
	
	def update_annotation(self, annotation):
		self.db.child(const.ANNOTATIONS).child(annotation.annotation_id).set(annotation.to_dict())
		logger.info(f"Updated annotation in the firebase - {annotation.__str__()}")
	
	def fetch_annotations(self):
		return self.db.child(const.ANNOTATIONS).get().val()
	
	def fetch_annotation(self, annotation_id):
		return self.db.child(const.ANNOTATIONS).child(annotation_id).get().val()
	
	def delete_annotation(self, annotation_id):
		logger.info(f"Deleting annotation {annotation_id} is withdrawn")
	
	# self.db.child(const.ANNOTATIONS).child(annotation_id).remove()
	
	# ---------------------- BEGIN NARRATION ----------------------
	def fetch_narration(self, recording_id):
		return self.db.child(const.NARRATIONS).child(recording_id).get().val()
	
	def update_narration(self, narration):
		self.db.child(const.NARRATIONS).child(narration.recording_id).set(narration.to_dict())
		logger.info(f"Updated narration in the firebase - {narration.__str__()}")


if __name__ == "__main__":
	db_service = FirebaseService()
