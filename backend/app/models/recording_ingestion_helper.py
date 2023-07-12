from typing import List, Optional

from ..models.error import Error
from ..models.step import Step
from ..utils.constants import DatabaseIngestion_Constants as const


class RecordingIngestionHelper:
	
	def __init__(
			self,
			recording_id: int,
			steps: List[Step],
			errors: Optional[List[Error]] = None
	):
		self.recording_id = recording_id
		
		self.steps = steps
		self.errors = errors
	
	def to_dict(self) -> dict:
		return {const.RECORDING_ID: self.recording_id,
		        const.STEPS: [step.to_dict() for step in self.steps],
		        const.ERRORS: [error.to_dict() for error in self.errors]}
	
	@classmethod
	def from_dict(cls, recording_helper_dict) -> "RecordingIngestionHelper":
		recording_id = recording_helper_dict[const.RECORDING_ID]
		steps = [Step.from_dict(step_dict) for step_dict in recording_helper_dict[const.STEPS]]
		
		errors = None
		if const.ERRORS in recording_helper_dict:
			errors = [Error.from_dict(error_dict) for error_dict in recording_helper_dict[const.ERRORS]]
		
		recording_helper = cls(recording_id, steps, errors)
		return recording_helper
