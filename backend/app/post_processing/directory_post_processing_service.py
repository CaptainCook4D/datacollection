import os

from .recording_post_processing_service import RecordingPostProcessingService
from ..models.recording import Recording
from ..utils.logger_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


class DirectoryPostProcessingService:

    def __init__(self, data_parent_directory=os.path.join(os.getcwd(), os.path.join('../../../../../', 'data'))):
        self.data_parent_directory = data_parent_directory

        self.hololens_parent_directory = os.path.join(self.data_parent_directory, 'hololens')
        self.gopro_parent_directory = os.path.join(self.data_parent_directory, 'gopro')

    def push_gopro_to_360p_directory(self, input_directory_path, output_directory_path):
        logger.info(f'Started changing video resolution and uploading to box for {input_directory_path}')

        # 1. List all the files in the directory
        gopro_videos = os.listdir(input_directory_path)

        # 2. Convert each video to 360p
        for input_video_name in gopro_videos:
            logger.info(f'Started changing video resolution and uploading to box for {input_video_name}')
            activity_id = int(input_video_name.split("_")[0])
            recording_instance = Recording(id=input_video_name[:-4], activity_id=activity_id, is_error=False, steps=[])
            input_video_file_path = os.path.join(input_directory_path, input_video_name)

            output_video_name = input_video_name.replace('.MP4', '_360p.mp4')
            output_video_file_path = os.path.join(output_directory_path, output_video_name)

            if os.path.exists(output_video_file_path):
                logger.info(f'File {output_video_file_path} already exists. Skipping.')
                continue

            recording_post_processing_service = RecordingPostProcessingService(recording_instance)
            recording_post_processing_service.push_go_pro_360_to_box(input_video_file_path, output_video_file_path)

            logger.info(f'Finished changing video resolution and uploading to box for {input_video_name}')

        logger.info(f'Finished changing video resolution and uploading to box for {input_directory_path}')

    def push_data_to_NAS(self):
        logger.info(f'Started pushing data to NAS')

        # 1. List all the files in the directory
        hololens_videos = os.listdir(self.hololens_parent_directory)
        gopro_videos = os.listdir(self.gopro_parent_directory)
        gopro_360p_videos = os.listdir(os.path.join(self.data_parent_directory, 'gopro_360p'))

        # 3. Upload each video to NAS
        # for gopro_video_name in gopro_videos:
        #     logger.info("----------------------------------------------------------------------------------------")
        #     logger.info(f'Started uploading to NAS for {gopro_video_name}')
        #     activity_id = int(gopro_video_name.split("_")[0])
        #     recording_instance = Recording(id=gopro_video_name[:-4], activity_id=activity_id, is_error=False, steps=[])
        #
        #     recording_post_processing_service = RecordingPostProcessingService(recording_instance, self.data_parent_directory)
        #     recording_post_processing_service.push_raw_data_to_NAS()
        #
        #     logger.info(f'Finished uploading to NAS for {gopro_video_name}')
        #     logger.info("----------------------------------------------------------------------------------------")

        for hololens_video_name in hololens_videos:
            logger.info("----------------------------------------------------------------------------------------")
            logger.info(f'Started uploading to NAS for {hololens_video_name}')
            activity_id = int(hololens_video_name.split("_")[0])
            recording_instance = Recording(id=hololens_video_name, activity_id=activity_id, is_error=False, steps=[])

            recording_post_processing_service = RecordingPostProcessingService(recording_instance, self.data_parent_directory)
            recording_post_processing_service.push_raw_data_to_NAS()

            logger.info(f'Finished uploading to NAS for {hololens_video_name}')
            logger.info("----------------------------------------------------------------------------------------")

        logger.info(f'Finished pushing data to NAS')
