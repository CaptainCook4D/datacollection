# 1. Transfer all local raw depth files from NAS to local machine
# 2. In the meantime, transfer the pose files and pv frames from raw to sync in NAS and transfer after zipping the frames
import os


def create_directory_if_not_exists(directory_path):
	if not os.path.exists(directory_path):
		os.makedirs(directory_path)


def transfer_raw_depth_files_from_nas_to_local(recording_id, remote_raw_directory_path, local_raw_directory_path):
	# 1. Transfer all raw zip files from NAS to local machine
	pv_zip_file_name = "pv.zip"
	
	# 2. Unzip all raw zip files in local machine
	
	# 3. Delete all raw zip files in local machine
	pass


def begin_nas_to_local_transfer():
	data_parent_directory = "/run/user/12345/gvfs/sftp:host=10.176.140.2/NetBackup/PTG"
	# recording_list = []
	# for data_recording_directory_name in os.listdir(data_parent_directory):
	# 	data_recording_directory_path = os.path.join(data_parent_directory, data_recording_directory_name)
	# 	if os.path.isdir(data_recording_directory_path):
	# 		raw_directory_path = os.path.join(data_recording_directory_path, "raw")
	# 		if os.path.isdir(raw_directory_path):
	# 			recording_list.append(data_recording_directory_path)
	recording_list = ["10_50"]
