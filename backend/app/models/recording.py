from typing import List, Optional

from ..models.error import Error
from ..models.recording_info import RecordingInfo
from ..models.step import Step

from ..utils.constants import Recording_Constants as const


class Recording:
	
	def __init__(
			self,
			id: str,
			activity_id: int,
			is_error: bool,
			steps: List[Step],
			errors: Optional[List[Error]] = None
	):
		self.id = id
		self.activity_id = activity_id
		self.is_error = is_error
		self.steps = steps
		self.errors = errors
		
		self.environment = None
		self.recorded_by = const.DUMMY_USER_ID
		
		self.is_prepared = False
		self.selected_by = const.DUMMY_USER_ID
		
		self.recording_info = RecordingInfo()
	
	def get_recording_id(self):
		return self.id
	
	def __str__(self):
		return f"Recording: ID: {self.id} - ACTIVITY: {self.activity_id} - IS_ERROR: {self.is_error} " \
		       f"- ENVIRONMENT: {self.environment} - RECORDED_BY: {self.recorded_by} - SELECTED_BY: {self.selected_by}"
	
	def update_parameters(self):
		if self.errors is not None and len(self.errors) > 0:
			self.is_error = True
		
		for step in self.steps:
			if step.errors is not None and len(step.errors) > 0:
				self.is_error = True
				break
		return
	
	def update_errors(self, recording_errors):
		if self.errors is None:
			self.errors = []
		self.errors.extend(recording_errors)
		if len(self.errors) > 10:
			self.is_prepared = True
	
	def to_dict(self) -> dict:
		recording_dict = {const.ID: self.id, const.ACTIVITY_ID: self.activity_id, const.IS_ERROR: self.is_error}
		
		step_dict_list = []
		for step in self.steps:
			step_dict_list.append(step.to_dict())
		recording_dict[const.STEPS] = step_dict_list
		
		if self.errors is not None and len(self.errors) > 0:
			error_dict_list = []
			for error in self.errors:
				error_dict_list.append(error.to_dict())
			recording_dict[const.ERRORS] = error_dict_list
		
		recording_dict[const.ENVIRONMENT] = self.environment
		recording_dict[const.RECORDED_BY] = self.recorded_by
		recording_dict[const.SELECTED_BY] = self.selected_by
		
		recording_dict[const.RECORDING_INFO] = self.recording_info.to_dict()
		
		if self.is_prepared:
			recording_dict[const.IS_PREPARED] = self.is_prepared
		
		return recording_dict
	
	@classmethod
	def from_dict(cls, recording_dict) -> "Recording":
		
		step_list = []
		for step_dict in recording_dict[const.STEPS]:
			step = Step.from_dict(step_dict)
			step_list.append(step)
		
		recording = cls(recording_dict[const.ID], recording_dict[const.ACTIVITY_ID], recording_dict[const.IS_ERROR],
		                step_list)
		
		if const.ERRORS in recording_dict:
			error_list = []
			for error_dict in recording_dict[const.ERRORS]:
				error = Error.from_dict(error_dict)
				error_list.append(error)
			recording.errors = error_list
		
		if const.ENVIRONMENT in recording_dict:
			recording.environment = recording_dict[const.ENVIRONMENT]
		
		if const.RECORDED_BY in recording_dict:
			recording.recorded_by = recording_dict[const.RECORDED_BY]
		
		if const.SELECTED_BY in recording_dict:
			recording.selected_by = recording_dict[const.SELECTED_BY]
		
		if const.IS_PREPARED in recording_dict:
			recording.is_prepared = recording_dict[const.IS_PREPARED]
		
		recording.recording_info = RecordingInfo.from_dict(recording_dict[const.RECORDING_INFO])
		return recording
