import json
from typing import Optional

from ..models.error import Error
from ..utils.constants import Recording_Constants as const


class Step:
	
	def __init__(
			self,
			description: str,
			modified_description: Optional[str] = None
	):
		self.description = description
		self.modified_description = modified_description
		
		self.errors = []
	
	# TODO: Check if it has to be replaced or extended
	def update_errors(self, step_errors):
		self.errors.extend(step_errors)
	
	def to_dict(self) -> dict:
		step_dict = {const.DESCRIPTION: self.description}
		
		if self.modified_description is not None:
			step_dict[const.MODIFIED_DESCRIPTION] = self.modified_description
		
		if len(self.errors) > 0:
			step_error_dict_list = []
			for step_error in self.errors:
				step_error_dict_list.append(step_error.to_dict())
			
			step_dict[const.ERRORS] = step_error_dict_list
		
		return step_dict
	
	@classmethod
	def from_dict(cls, step_dict) -> "Step":
		step = cls(step_dict[const.DESCRIPTION])
		
		if const.MODIFIED_DESCRIPTION in step_dict:
			step.modified_description = step_dict[const.MODIFIED_DESCRIPTION]
		
		if const.ERRORS in step_dict:
			step_errors_list = []
			for step_error_dict in step_dict[const.ERRORS]:
				step_error = Error.from_dict(step_error_dict)
				step_errors_list.append(step_error)
			step.errors = step_errors_list
		
		return step
	
	def __str__(self):
		return json.dumps(self.to_dict())
