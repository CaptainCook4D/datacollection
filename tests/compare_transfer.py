import os
import shutil


#
# def compare_files_in_folder(source_root, destination_root):
# 	# 1. Get all the files in the source folder and destination folder and compare them
# 	source_files = [f for f in os.listdir(source_root) if os.path.isfile(os.path.join(source_root, f))]
#
# 	for file in source_files:
# 		source_file = os.path.join(source_root, file)
# 		destination_file = os.path.join(destination_root, file)
#
# 		if not os.path.isfile(destination_file):
# 			print(f"File {destination_file} is missing.")
# 			return False
#
# 		if os.path.getsize(source_file) != os.path.getsize(destination_file):
# 			print(f"File {destination_file} has a different size.")
# 			return False
#
# 	return True
#
#
# def compare_folders(source_root, destination_root):
# 	# 1. Check if all files in the source folder are present in the destination folder
# 	are_files_matching = compare_files_in_folder(source_root, destination_root)
#
# 	if not are_files_matching:
# 		print("-----------------------------------")
# 		print("Files are missing.")
# 		print("Source folder: ", source_root)
# 		print("Destination folder: ", destination_root)
# 		print("-----------------------------------")
# 		return False
#
# 	# 2. Get all the sub folders in the source folder and destination folder and compare them recursively
# 	source_directories = [d for d in os.listdir(source_root) if os.path.isdir(os.path.join(source_root, d))]
# 	destination_directories = [d for d in os.listdir(destination_root) if
# 	                           os.path.isdir(os.path.join(destination_root, d))]
#
# 	for directory in source_directories:
# 		source_directory = os.path.join(source_root, directory)
# 		destination_directory = os.path.join(destination_root, directory)
#
# 		if not os.path.isdir(destination_directory):
# 			print(f"Directory {destination_directory} is missing.")
# 			return False
#
# 		are_folders_matching = compare_folders(source_directory, destination_directory)
#
# 		if not are_folders_matching:
# 			print("-----------------------------------")
# 			print("Folder files are missing.")
# 			print("Source folder: ", source_directory)
# 			print("Destination folder: ", destination_directory)
# 			print("-----------------------------------")
# 			return False


def compare_and_transfer_info_files(source_parent_directory, destination_parent_directory):
    for recording_id in os.listdir(source_parent_directory):
        print("----------------------------------------------------------")
        print(f"Processing recording {recording_id}")
        source_recording_directory = os.path.join(source_parent_directory, recording_id)
        if os.listdir(source_recording_directory):
            source_recording_info_file_path = os.path.join(source_recording_directory, "Hololens2Info.dat")
            destination_recording_folder = os.path.join(destination_parent_directory, recording_id, "raw")
            destination_recording_info_file_path = os.path.join(destination_recording_folder, "Hololens2Info.dat")

            if not os.path.isdir(destination_recording_folder):
                print("Recording folder does not exist. Skipping this recording.")
                continue

            if os.path.isfile(source_recording_info_file_path):
                if not os.path.isfile(destination_recording_info_file_path):
                    print(f"Copying file {destination_recording_info_file_path}")
                    shutil.copyfile(source_recording_info_file_path, destination_recording_info_file_path)
                else:
                    if os.path.getsize(source_recording_info_file_path) != os.path.getsize(
                            destination_recording_info_file_path):
                        print(f"File {destination_recording_info_file_path} has a different size.")
                        print("Deleting the file and copying again.")
                        shutil.rmtree(destination_recording_info_file_path)
                        shutil.copyfile(source_recording_info_file_path, destination_recording_info_file_path)
                    print(f"File {destination_recording_info_file_path} already exists.")


if __name__ == '__main__':
    source_directory = "/run/user/12345/gvfs/sftp:host=10.176.140.2/NetBackup/BACKUP_STUFF/PTG_HOLOLENS_BACKUP/hololens_bak_bharath"
    destination_directory = "/run/user/12345/gvfs/sftp:host=10.176.140.2/NetBackup/PTG"

    compare_and_transfer_info_files(source_directory, destination_directory)
