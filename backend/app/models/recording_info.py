import json

from .hololens_info import HololensInfo
from ..utils.constants import Recording_Constants as const


class RecordingInfo:
	
	def __init__(self):
		self.go_pro = True
		self.hololens_info = HololensInfo()
		
		self.start_time = None
		self.end_time = None
		
	def to_dict(self):
		return {
			const.GOPRO: self.go_pro,
			const.HOLOLENS_INFO: self.hololens_info.to_dict(),
			const.START_TIME: json.dumps(self.start_time),
			const.END_TIME: json.dumps(self.end_time)
		}
	
	def is_go_pro_enabled(self):
		return self.go_pro
	
	def is_hololens_enabled(self):
		return self.hololens_info.is_enabled()
	
	@classmethod
	def from_dict(cls, recording_info_dict):
		recording_info = cls()
		
		recording_info.go_pro = recording_info_dict[const.GOPRO]
		recording_info.hololens_info = HololensInfo.from_dict(recording_info_dict[const.HOLOLENS_INFO])
		
		if const.START_TIME in recording_info_dict:
			recording_info.start_time = json.loads(recording_info_dict[const.START_TIME])
			
		if const.END_TIME in recording_info_dict:
			recording_info.end_time = json.loads(recording_info_dict[const.END_TIME])
		
		return recording_info
	
	def __str__(self):
		return json.dumps(self.to_dict())
