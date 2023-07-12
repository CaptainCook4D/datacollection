import os
import pickle


def verify_data():
    data_parent_directory = "/run/user/12345/gvfs/sftp:host=10.176.140.2/NetBackup/PTG"
    data_recording_directories = os.listdir(data_parent_directory)

    for data_recording_name in data_recording_directories:
        data_recording_directory = os.path.join(data_parent_directory, data_recording_name)
        if os.path.isdir(data_recording_directory):
            raw_data_directory = os.path.join(data_recording_directory, "raw")
            pv_data_directory = os.path.join(raw_data_directory, "pv")
            if os.path.isdir(pv_data_directory):
                pv_data_file = os.path.join(pv_data_directory, f"{data_recording_name}_pv_pose.pkl")
                with open(pv_data_file, 'rb') as f:
                    pv_data = pickle.load(f)
                    print(pv_data)
                    
                    
def verify_pkl_data():
    pkl_file_path = r"D:\DATA\OPEN\ActionGenome\action_genome_v1.0\person_bbox.pkl"
    with open(pkl_file_path, 'rb') as f:
        pkl_data = pickle.load(f)
        print(pkl_data)


if __name__ == '__main__':
    verify_pkl_data()
