import os
import shutil
import time

from ..utils.constants import Post_Processing_Constants as ppc_const
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class CompressDataService:
	# AB = 'ab'
	# DEPTH = 'depth'
	# DEPTH_AHAT = 'depth_ahat'
	# FRAMES = 'frames'
	# PV = 'pv'
	# ZIP = 'zip'
	
	def __init__(self, data_dir, depth_dir_name=ppc_const.DEPTH_AHAT, pv_dir_name=ppc_const.PHOTOVIDEO):
		self.data_dir = data_dir
		self.depth_root_dir = os.path.join(self.data_dir, depth_dir_name)
		self.pv_dir = os.path.join(self.data_dir, pv_dir_name)
	
	@classmethod
	def compress_dir(cls, base_dir_path, file_name, root_dir=None, compress_format=ppc_const.ZIP):
		if root_dir is None:
			root_dir = base_dir_path
		file_path = os.path.join(root_dir, file_name)
		file_count = len(os.listdir(file_path))
		
		logger.info(f'Archiving {root_dir} - {file_name} ({file_count} files) STARTED')
		start_time = time.time()
		shutil.make_archive(base_name=file_path, format=compress_format, root_dir=root_dir, base_dir=file_path)
		end_time = time.time()
		logger.info(f'Archiving {root_dir} - {file_name} ({file_count} files) FINISHED')
		logger.info(f'Archive {file_path}.zip ({file_count} files) took {(end_time - start_time):.2f} seconds')
	
	@classmethod
	def delete_dir(cls, dir_path):
		logger.info(f'Deleting directory {dir_path} STARTED')
		start_time = time.time()
		shutil.rmtree(dir_path)
		end_time = time.time()
		logger.info(f'Deleting directory {dir_path} FINISHED')
		logger.info(f'Deleting directory {dir_path} took {(end_time - start_time):.2f} seconds')
	
	def compress_depth(self):
		depth_dir = os.path.join(self.depth_root_dir, ppc_const.DEPTH)
		ab_dir = os.path.join(self.depth_root_dir, ppc_const.AB)
		self.compress_dir(depth_dir, ppc_const.DEPTH, self.depth_root_dir)
		self.compress_dir(ab_dir, ppc_const.AB, self.depth_root_dir)
	
	def compress_pv(self):
		frames_dir = os.path.join(self.pv_dir, ppc_const.FRAMES)
		self.compress_dir(frames_dir, ppc_const.FRAMES, self.pv_dir)
	
	def delete_depth_dir(self):
		depth_dir = os.path.join(self.depth_root_dir, ppc_const.DEPTH)
		ab_dir = os.path.join(self.depth_root_dir, ppc_const.AB)
		self.delete_dir(depth_dir)
		self.delete_dir(ab_dir)
	
	def delete_pv_dir(self):
		frames_dir = os.path.join(self.pv_dir, ppc_const.FRAMES)
		self.delete_dir(frames_dir)


if __name__ == '__main__':
	cds = CompressDataService(data_dir='../../../../../data/hololens/13_43')
	cds.compress_depth()
	cds.compress_pv()
