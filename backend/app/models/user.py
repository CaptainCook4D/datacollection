import random
import json

from typing import List
from ..utils.constants import User_Constants as const
from ..models.schedule import Schedule
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class User:
	
	def __init__(self, id, username):
		self.id = id
		self.username = username
		
		self.activity_preferences = set()
		self.recording_schedules = {}
	
	def update_preferences(self, activity_list: List[int]):
		self.activity_preferences = self.activity_preferences | set(activity_list)
	
	def update_recording(self, environment: int, activity_id):
		if environment in self.recording_schedules:
			environment_schedule = self.recording_schedules[environment]
			environment_schedule.update_recorded(activity_id)
		else:
			logger.error("Current environment schedule is not created")
			raise Exception("Current environment schedule is not created")
	
	def update_environment_schedule(self, environment: int):
		# Create/Update a schedule for this environment
		if len(self.activity_preferences) == 0:
			logger.error("Preferences are not set - set preferences first")
			raise Exception("Preferences are not set - set preferences first")
		
		# 1. Fetch all the recorded activities till now
		previous_recordings = set()
		previous_environments = range(1, environment + 1)
		for prev_environment in previous_environments:
			if not self.recording_schedules:
				break
			elif prev_environment not in self.recording_schedules:
				continue
			previous_recordings = previous_recordings | set(self.recording_schedules[prev_environment].recorded_list)
		
		# 2. From the activity preferences remove them - can also be empty set
		activities_not_recorded = set(self.activity_preferences) - previous_recordings
		
		# 3. Add them to the last of the environment preferences list
		environment_preferences = list(activities_not_recorded) + list(previous_recordings)
		
		# 4. Repeat preferences if they are less
		env_pref_len = len(environment_preferences)
		if env_pref_len < const.ACTIVITIES_PER_PERSON_PER_ENV:
			for idx in range(0, const.ACTIVITIES_PER_PERSON_PER_ENV - env_pref_len):
				environment_preferences.append(random.choice(environment_preferences))
		else:
			random.shuffle(environment_preferences)
			environment_preferences = environment_preferences[:const.ACTIVITIES_PER_PERSON_PER_ENV]
		
		# 5. Sample the first half for normal videos
		# 6. Second half for the error videos
		random.shuffle(environment_preferences)
		normal_recordings = environment_preferences[:int(const.ACTIVITIES_PER_PERSON_PER_ENV / 2.)]
		error_recordings = environment_preferences[int(const.ACTIVITIES_PER_PERSON_PER_ENV / 2.):]
		
		schedule = Schedule(environment=environment, normal_recordings=normal_recordings,
		                    error_recordings=error_recordings)
		
		self.recording_schedules[environment] = schedule
	
	def build_all_environment_schedules(self):
		all_environments = range(1, const.TOTAL_ENVIRONMENTS + 1)
		recorded_environments = []
		if len(self.recording_schedules) > 0:
			recorded_environments = [environment for environment in self.recording_schedules if
			                         self.recording_schedules[environment].is_done_recording]
		
		environments_yet_to_record = list(set(all_environments) - set(recorded_environments))
		
		for environment in environments_yet_to_record:
			self.update_environment_schedule(environment)
	
	def to_dict(self) -> dict:
		user_dict = {const.ID: self.id, const.USERNAME: self.username}
		
		if len(self.activity_preferences) > 0:
			user_dict[const.ACTIVITY_PREFERENCES] = list(self.activity_preferences)
		
		if len(self.recording_schedules) > 0:
			environment_to_schedule = self.recording_schedules
			environment_to_schedule_dict = {}
			for environment in environment_to_schedule:
				environment_to_schedule_dict[environment] = environment_to_schedule[environment].to_dict()
			
			user_dict[const.RECORDING_SCHEDULES] = environment_to_schedule_dict
		
		return user_dict
	
	@classmethod
	def from_dict(cls, user_dict) -> "User":
		user = User(user_dict[const.ID], user_dict[const.USERNAME])
		
		if const.ACTIVITY_PREFERENCES in user_dict:
			user.activity_preferences = set(user_dict[const.ACTIVITY_PREFERENCES])
		
		if const.RECORDING_SCHEDULES in user_dict:
			recording_schedules_dict_list = user_dict[const.RECORDING_SCHEDULES]
			for schedule_dict in recording_schedules_dict_list:
				if schedule_dict is not None:
					schedule = Schedule.from_dict(schedule_dict)
					user.recording_schedules[schedule_dict[const.ENVIRONMENT]] = schedule
		return user
	
	def __str__(self):
		return json.dumps(self.to_dict())
