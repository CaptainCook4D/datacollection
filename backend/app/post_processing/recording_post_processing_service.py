# TODO:
# 1. Each method takes a list of directories as input
# 2. Performs the necessary function as described by the method name
import os

from .sequence_viewer import SequenceViewer
from .compress_data_service import CompressDataService
from .nas_transfer_service import NASTransferService
from .synchronization_service import SynchronizationService
from .video_conversion_service import VideoConversionService
from ..utils.constants import Post_Processing_Constants as const
from ..services.box_service import BoxService
from ..services.firebase_service import FirebaseService
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class RecordingPostProcessingService:
	
	def __init__(
			self,
			recording,
			data_parent_directory=os.path.join(os.getcwd(), os.path.join('..', 'data'))
	):
		self.recording = recording
		self.data_parent_directory = data_parent_directory
		
		self.hololens_parent_directory = os.path.join(self.data_parent_directory, const.HOLOLENS)
		self.hololens_data_directory = os.path.join(self.hololens_parent_directory, self.recording.id)
		self.synchronized_data_directory = os.path.join(self.hololens_data_directory, const.SYNC)
		
		self.box_service = BoxService()
		self.db_service = FirebaseService()
		self.nas_transfer_service = NASTransferService(self.recording, self.data_parent_directory)
	
	def change_video_resolution(self, video_file_path, output_file_path, resolution=None):
		logger.info(f'Started changing video resolution for {self.recording.id}')
		video_conversion_service = VideoConversionService()
		converted_file_path = video_conversion_service.convert_video(video_file_path, output_file_path)
		logger.info(f'Finished changing video resolution for {self.recording.id}')
		return converted_file_path
	
	def synchronize_data(self):
		base_stream = const.PHOTOVIDEO
		sync_streams = [const.DEPTH_AHAT, const.SPATIAL]
		pv_sync_stream = SynchronizationService(
			base_stream=base_stream,
			synchronize_streams=sync_streams,
			hololens_parent_directory=self.hololens_parent_directory,
			synchronized_data_directory=self.synchronized_data_directory,
			recording=self.recording
		)
		logger.info(f'Started synchronization for {self.recording.id}')
		pv_sync_stream.sync_streams()
		logger.info(f'Finished synchronization for {self.recording.id}')
	
	def compress_data(self):
		# Compress the data
		logger.info(f'Started compressing data for {self.recording.id}')
		cds = CompressDataService(data_dir=self.hololens_data_directory)
		sync_cds = CompressDataService(data_dir=self.synchronized_data_directory)
		cds.compress_depth()
		cds.compress_pv()
		sync_cds.compress_depth()
		sync_cds.compress_pv()
		logger.info(f'Finished compressing data for {self.recording.id}')
	
	def delete_uncompressed_data(self):
		# Delete the uncompressed data
		logger.info(f'Started deleting uncompressed data for {self.recording.id}')
		cds = CompressDataService(data_dir=self.hololens_data_directory)
		sync_cds = CompressDataService(data_dir=self.synchronized_data_directory)
		cds.delete_pv_dir()
		cds.delete_depth_dir()
		sync_cds.delete_pv_dir()
		sync_cds.delete_depth_dir()
		logger.info(f'Finished deleting uncompressed data for {self.recording.id}')

	def compress_raw_data(self):
		# Compress the data
		logger.info(f'Started compressing data for {self.recording.id}')
		cds = CompressDataService(data_dir=self.hololens_data_directory)
		cds.compress_depth()
		cds.compress_pv()
		logger.info(f'Finished compressing data for {self.recording.id}')

	def delete_uncompressed_raw_data(self):
		# Delete the uncompressed data
		logger.info(f'Started deleting uncompressed data for {self.recording.id}')
		cds = CompressDataService(data_dir=self.hololens_data_directory)
		cds.delete_pv_dir()
		cds.delete_depth_dir()
		logger.info(f'Finished deleting uncompressed data for {self.recording.id}')

	def verify_3d_information(self):
		sequence_folder = os.path.join(self.data_parent_directory, self.recording.id, const.SYNC)
		sequence_viewer = SequenceViewer()
		sequence_viewer.load(sequence_folder)
		sequence_viewer.run()
	
	def push_go_pro_360_to_box(self, input_file_path, output_file_path=None):
		output_file_path = self.change_video_resolution(input_file_path, output_file_path)
		self.box_service.upload_go_pro_360_video(self.recording, output_file_path)

	def push_raw_data_to_NAS(self):
		try:
			self.compress_raw_data()
		except FileNotFoundError:
			logger.info(f'No raw data found for {self.recording.id}')
			return

		self.delete_uncompressed_raw_data()
		self.nas_transfer_service.transfer_from_local_to_nas()

	def push_data_to_NAS(self):
		self.compress_raw_data()
		self.delete_uncompressed_raw_data()
		self.nas_transfer_service.transfer_from_local_to_nas()
	
	def process_and_push_data_to_nas(self):
		self.synchronize_data()
		self.compress_data()
		self.delete_uncompressed_data()
		self.push_data_to_NAS()
	
	def push_NAS_data_to_box(self):
		pass
	
	def generate_audio(self):
		pass
	
	def generate_video(self):
		pass
	
	def generate_muxed_audio_video(self):
		pass
