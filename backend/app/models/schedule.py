import json
from typing import List, Optional
from ..utils.constants import User_Constants as const


class Schedule:
	
	def __init__(
			self,
			environment: int,
			normal_recordings: List[int] = [],
			error_recordings: List[int] = []
	):
		self.normal = normal_recordings
		self.errors = error_recordings
		self.environment = environment
		
		self.recorded_list = []
		self.is_done_recording = False
	
	def update_recorded(self, activity_id):
		self.recorded_list.append(activity_id)
		
		if activity_id in self.normal:
			self.normal.remove(activity_id)
		
		if activity_id in self.errors:
			self.errors.remove(activity_id)
		
		if len(self.recorded_list) >= 8:
			self.is_done_recording = True
	
	def to_dict(self) -> dict:
		schedule_dict = {const.ENVIRONMENT: self.environment}

		if self.normal is not None and self.normal.__len__() > 0:
			schedule_dict[const.NORMAL_RECORDINGS] = self.normal

		if self.errors is not None and self.errors.__len__() > 0:
			schedule_dict[const.ERROR_RECORDINGS] = self.errors
		
		if len(self.recorded_list) > 0:
			schedule_dict[const.RECORDED_LIST] = self.recorded_list
			schedule_dict[const.IS_DONE_RECORDING] = self.is_done_recording
		
		return schedule_dict
	
	@classmethod
	def from_dict(cls, schedule_dict) -> "Schedule":
		schedule = Schedule(schedule_dict[const.ENVIRONMENT])

		if const.NORMAL_RECORDINGS in schedule_dict:
			schedule.normal = schedule_dict[const.NORMAL_RECORDINGS]

		if const.ERROR_RECORDINGS in schedule_dict:
			schedule.errors = schedule_dict[const.ERROR_RECORDINGS]
		
		if const.RECORDED_LIST in schedule_dict:
			schedule.recorded_list = schedule_dict[const.RECORDED_LIST]
			schedule.is_done_recording = schedule_dict[const.IS_DONE_RECORDING]
		
		return schedule
	
	def __str__(self):
		return json.dumps(self.to_dict())