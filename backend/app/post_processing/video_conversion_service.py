import shlex
import subprocess
import time

from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class VideoConversionService:
	FFMPEG_PATH = '/usr/bin/ffmpeg'
	RES_360P = '360p'
	RES_720P = '720p'
	RES_1080P = '1080p'
	
	RES_MAP = {
		RES_360P: {
			'width': 640,
			'height': 360
		},
		RES_720P: {
			'width': 1280,
			'height': 720
		},
		RES_1080P: {
			'width': 1920,
			'height': 1080
		},
	}
	
	# Example:          ffmpeg -i -y -hwaccel cuda input_vd.MP4 -vf scale=640:360 -c:a copy output_vd.mp4
	# FFMPEG_COMMAND = 'ffmpeg -i -y -hwaccel cuda {input_file} -vf scale={scale} -c:a copy {output_file}'
	FFMPEG_COMMAND = '{} -y -hwaccel cuda -i {} -vf scale={} -c:a copy {}'
	
	def __init__(self, ffmpeg_path=FFMPEG_PATH):
		self.ffmpeg_path = ffmpeg_path
	
	def get_ffmpeg_scale(self, conversion_type):
		return f'{self.RES_MAP[conversion_type]["width"]}:{self.RES_MAP[conversion_type]["height"]}'
	
	def convert_video(self, video_file_path, output_file_path=None, conversion_type=RES_360P):
		if output_file_path is None:
			converted_video_file_path = video_file_path.replace('.MP4', f'_{conversion_type}.mp4')
		else:
			converted_video_file_path = output_file_path
		
		convert_command = self.FFMPEG_COMMAND.format(
			self.ffmpeg_path,
			video_file_path,
			self.get_ffmpeg_scale(conversion_type),
			converted_video_file_path,
		)
		start_time = time.time()
		logger.info(f'FFMPEG command: {convert_command}')
		subprocess.call(shlex.split(convert_command))
		end_time = time.time()
		logger.info(f'Conversion took {(end_time - start_time):.2f} seconds')
		return converted_video_file_path


if __name__ == '__main__':
	cgv = VideoConversionService()
	cgv.convert_video(video_file_path='../../../../../data/gopro/13_43.MP4')
