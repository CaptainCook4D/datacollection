from ..utils.constants import Narration_Constants as const


class Narration:
	
	def __init__(self, recording_id, narration_json):
		self._recording_id = recording_id
		self._narration_json = narration_json
	
	def get_narration(self):
		return self._narration_json
	
	def get_recording_id(self):
		return self._recording_id
	
	@classmethod
	def from_dict(cls, narration_dict) -> "Narration":
		narration = cls(narration_dict[const.RECORDING_ID], narration_dict[const.NARRATION_JSON])
		return narration
	
	def to_dict(self):
		narration_dict = {const.RECORDING_ID: self._recording_id, const.NARRATION_JSON: self._narration_json}
		return narration_dict
