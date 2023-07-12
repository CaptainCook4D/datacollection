from .video_conversion_service import VideoConversionService
from ..services.box_service import BoxService
from ..utils.constants import Post_Processing_Constants as const

import os

from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class NasToBoxPostProcessingService:
	
	def __init__(self, recording):
		self.recording = recording
		self.box_service = BoxService()
		
		self.nas_root_directory = const.NAS_DATA_ROOT_DIR
		self.nas_recording_parent_directory = os.path.join(self.nas_root_directory, self.recording.id)
		
		self.nas_recording_gopro_directory = os.path.join(self.nas_recording_parent_directory, const.GOPRO)
		
		self.gopro_video_name = f'{self.recording.id}.MP4'
		self.gopro_video_360p_name = f'{self.recording.id}_360p.MP4'
		self.gopro_video_file_path = os.path.join(self.nas_recording_gopro_directory, self.gopro_video_name)
		self.gopro_video_360p_file_path = os.path.join(self.nas_recording_gopro_directory, self.gopro_video_360p_name)
	
	def convert_gopro_to_360p(self):
		self.change_video_resolution(self.gopro_video_file_path, self.gopro_video_360p_file_path)
	
	def transfer_gopro_360p_to_box(self):
		self.box_service.upload_go_pro_360_video(self.recording, self.gopro_video_360p_file_path)
	
	def change_video_resolution(self, video_file_path, output_file_path, resolution=None):
		logger.info(f'Started changing video resolution for {self.recording.id}')
		video_conversion_service = VideoConversionService()
		converted_file_path = video_conversion_service.convert_video(video_file_path, output_file_path)
		logger.info(f'Finished changing video resolution for {self.recording.id}')
		return converted_file_path
	
	def synchronize_data(self):
		pass
	
	def raw_data_to_box(self):
		pass
	
	def sync_data_to_box(self):
		pass
