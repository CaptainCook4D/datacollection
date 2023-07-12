import logging
import os
import pickle
import shutil
from typing import List

import cv2

from ..hololens import hl2ss
from ..models.recording import Recording
from ..utils.constants import Post_Processing_Constants as ppc_const
from ..post_processing.compress_data_service import CompressDataService
from ..utils.logger_config import get_logger

logger = get_logger(__name__)
UNIX_EPOCH = 11644473600


def create_directories(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def write_pickle_data(pickle_data, pickle_file_path):
    with open(pickle_file_path, 'wb') as pickle_file:
        pickle.dump(pickle_data, pickle_file)


def read_stream_pkl_data(stream_pkl_file_path):
    pkl_frames = []
    with open(stream_pkl_file_path, 'rb') as stream_file:
        while stream_file.seekable():
            try:
                pkl_frames.append(pickle.load(stream_file))
            except EOFError:
                break
    return pkl_frames


def get_nearest_timestamp(data, timestamp):
    n = len(data)
    if n <= 0:
        return None
    elif n == 1:
        return 0
    left, right = 0, n - 1

    while (right - left) > 1:
        i = (right + left) // 2
        t = data[i]
        if t < timestamp:
            left = i
        elif t > timestamp:
            right = i
        else:
            return i
    idx = left if (abs(data[left] - timestamp) < abs(data[right] - timestamp)) else right
    # Need to check the time difference must not be more than a second. If it is return None
    return None if (abs(data[idx] - timestamp) > 1e8) else idx


def get_timestamp_to_stream_frame(
        stream_directory,
        stream_extension,
        timestamp_index=-1
):
    stream_extension_length = len(stream_extension)
    stream_frames = [frame for frame in os.listdir(stream_directory) if frame.endswith(stream_extension)]

    def get_timestamp_from_stream_file_name(stream_file_name):
        _splits = (stream_file_name[:-stream_extension_length].split("_"))
        if _splits[timestamp_index] == "depth" or _splits[timestamp_index] == "ab":
            return int(_splits[timestamp_index - 1])
        return int(_splits[timestamp_index])

    stream_frames = sorted(stream_frames, key=lambda x: get_timestamp_from_stream_file_name(x))

    timestamp_to_stream_frame = {}
    for stream_frame in stream_frames:
        timestamp = get_timestamp_from_stream_file_name(stream_frame)
        timestamp_to_stream_frame[timestamp] = stream_frame

    return timestamp_to_stream_frame


class SynchronizationService:

    def __init__(
            self,
            base_stream: str,
            synchronize_streams: List[str],
            hololens_parent_directory: str,
            synchronized_data_directory: str,
            recording: Recording
    ):
        self.base_stream = base_stream
        self.synchronize_streams = synchronize_streams
        self.hololens_parent_directory = hololens_parent_directory
        self.synchronized_data_directory = synchronized_data_directory
        self.recording = recording
        self.recording_id = self.recording.get_recording_id()

        self.data_directory = os.path.join(self.hololens_parent_directory, self.recording_id)
        self.synchronized_directory = self.synchronized_data_directory

        self.base_stream_directory = os.path.join(self.data_directory, self.base_stream)
        self.synchronized_base_stream_directory = os.path.join(self.synchronized_directory, self.base_stream)

        self.timestamp_to_base_stream_frame = None
        self.base_stream_keys = None

        self.pv_stream_suffix = "color-%06d.jpg"
        self.depth_stream_suffix = "depth-%06d.png"
        self.ab_stream_suffix = "ab-%06d.png"
        self.vlc_stream_suffix = "vlc-%06d.jpg"

        self.num_of_frames = 0
        self.depth_mode = None
        self.depth_width = None
        self.depth_height = None
        self.pv_width = None
        self.pv_height = None

    def get_device_id(self):
        hololens_info_file = os.path.join(self.data_directory, ppc_const.HOLOLENS_INFO_FILE_NAME)
        with open(hololens_info_file, 'r') as f:
            hololens_info_data = f.readlines()
        for line in hololens_info_data:
            if line.startswith("Hololens2 Name"):
                return line.split(":")[1].strip()

    def get_width_height(self, image_path):
        image = cv2.imread(image_path)
        return image.shape[1], image.shape[0]

    def create_synchronized_stream_pkl_data(self, stream_pkl_file_path, synchronized_stream_output_directory):
        # 1. Load pickle file data into a dictionary
        timestamp_to_stream_payload = {}
        pkl_frames = read_stream_pkl_data(stream_pkl_file_path)
        for pkl_frame in pkl_frames:
            # TODO: Remove the else part after the pickle file is fixed
            ts, payload = pkl_frame if type(pkl_frame) is tuple else (pkl_frame.timestamp, pkl_frame.payload)
            if type(payload) is bytearray:
                payload = hl2ss.unpack_si(payload)
            timestamp_to_stream_payload[ts] = payload
        # 2. Use the base_stream_keys and loaded pickle file data to synchronize them
        stream_keys = sorted(timestamp_to_stream_payload.keys())
        synced_timestamp_to_stream_payload = {}
        for base_stream_key in self.base_stream_keys:
            stream_ts_idx = get_nearest_timestamp(stream_keys, base_stream_key)
            stream_timestamp = stream_keys[stream_ts_idx]
            stream_payload = timestamp_to_stream_payload[stream_timestamp]
            synced_timestamp_to_stream_payload[base_stream_key] = (stream_payload, stream_timestamp)
        # TODO: Add a logger statement here
        write_pickle_data(synced_timestamp_to_stream_payload, synchronized_stream_output_directory)

    def create_synchronized_stream_frames(self, stream_directory, stream_extension,
                                          synchronized_stream_output_directory, stream_suffix):
        timestamp_to_stream_frame = get_timestamp_to_stream_frame(stream_directory, stream_extension)
        stream_keys = sorted(timestamp_to_stream_frame.keys())

        for base_stream_counter, base_stream_key in enumerate(self.base_stream_keys):
            stream_ts_idx = get_nearest_timestamp(stream_keys, base_stream_key)
            stream_timestamp = stream_keys[stream_ts_idx]
            shutil.copy(os.path.join(stream_directory, timestamp_to_stream_frame[stream_timestamp]),
                        os.path.join(synchronized_stream_output_directory, stream_suffix % base_stream_counter))
        return

    # TODO: Complete code when Microphone data is considered as base stream for synchronization
    # --------- Base streams: PV, Microphone
    # --------- Synchronize Streams: PV, Depth-Ahat, Depth-Lt, Spatial, VLC frames
    # a. Depth cannot be base stream
    # b. If Microphone is base stream, we can duplicate frame and artificially increase frame rate of video
    # 1. Get base stream timestamps, associated files
    # 2. In a for loop, check for each of the synchronize streams
    # 3. Based on the stream, synchronize Pose, Payload -- if depth then synchronize ab and depth frames
    def sync_streams(self):
        # meta.yaml file data
        meta_yaml_data = {}
        device_id = self.get_device_id()
        meta_yaml_data["device_id"] = device_id
        if self.base_stream == ppc_const.PHOTOVIDEO:
            # 1. Create base stream keys used to synchronize the rest of the data
            base_stream_frames_dir = os.path.join(self.base_stream_directory, "frames")
            self.timestamp_to_base_stream_frame = get_timestamp_to_stream_frame(base_stream_frames_dir,
                                                                                stream_extension=".jpg",
                                                                                timestamp_index=-1)
            self.base_stream_keys = sorted(self.timestamp_to_base_stream_frame.keys())
            self.num_of_frames = len(self.base_stream_keys)
            meta_yaml_data["num_of_frames"] = self.num_of_frames
            synchronized_base_stream_frames_dir = os.path.join(self.synchronized_base_stream_directory, "frames")
            create_directories(synchronized_base_stream_frames_dir)
            sample_base_stream_frame = os.path.join(base_stream_frames_dir, os.listdir(base_stream_frames_dir)[0])
            self.pv_width, self.pv_height = self.get_width_height(sample_base_stream_frame)
            meta_yaml_data["pv_width"] = self.pv_width
            meta_yaml_data["pv_height"] = self.pv_height

            # 2. Copy base stream frames into the synchronized output folder
            for base_stream_counter, base_stream_key in enumerate(self.base_stream_keys):
                src_file = os.path.join(base_stream_frames_dir,
                                        self.timestamp_to_base_stream_frame[base_stream_key])
                dest_file = os.path.join(synchronized_base_stream_frames_dir,
                                         self.pv_stream_suffix % base_stream_counter)
                shutil.copy(src_file, dest_file)
            # Synchronize PV Pose
            pv_pose_pkl = f'{self.recording.id}_pv_pose.pkl'
            pv_pose_file_path = os.path.join(self.base_stream_directory, pv_pose_pkl)
            sync_pv_pose_file_path = os.path.join(self.synchronized_base_stream_directory, pv_pose_pkl)
            self.create_synchronized_stream_pkl_data(pv_pose_file_path, sync_pv_pose_file_path)

            for stream_name in self.synchronize_streams:
                if stream_name == ppc_const.DEPTH_AHAT:
                    depth_parent_directory = os.path.join(self.data_directory, ppc_const.DEPTH_AHAT)
                    synchronized_depth_parent_directory = os.path.join(self.synchronized_directory,
                                                                       ppc_const.DEPTH_AHAT)
                    create_directories(synchronized_depth_parent_directory)

                    # 1. Synchronize Pose
                    depth_ahat_pkl = f'{self.recording.id}_depth_ahat_pose.pkl'
                    depth_pose_file_path = os.path.join(depth_parent_directory, depth_ahat_pkl)
                    sync_depth_pose_file_path = os.path.join(synchronized_depth_parent_directory, depth_ahat_pkl)
                    self.create_synchronized_stream_pkl_data(depth_pose_file_path, sync_depth_pose_file_path)

                    # 2. Synchronize Depth data
                    # ToDo: change it to DEPTH variables
                    depth_data_directory = os.path.join(depth_parent_directory, ppc_const.DEPTH)
                    synchronized_depth_data_directory = os.path.join(synchronized_depth_parent_directory,
                                                                     ppc_const.DEPTH)
                    create_directories(synchronized_depth_data_directory)
                    self.create_synchronized_stream_frames(depth_data_directory, ".png",
                                                           synchronized_depth_data_directory, self.depth_stream_suffix)

                    # 3. Synchronize Active Brightness data
                    # ToDo: change it to AB variables
                    depth_ab_directory = os.path.join(depth_parent_directory, ppc_const.AB)
                    synchronized_depth_ab_directory = os.path.join(synchronized_depth_parent_directory, ppc_const.AB)
                    create_directories(synchronized_depth_ab_directory)
                    self.create_synchronized_stream_frames(depth_ab_directory, ".png",
                                                           synchronized_depth_ab_directory, self.ab_stream_suffix)
                    sample_depth_frame = os.path.join(depth_data_directory, os.listdir(depth_data_directory)[0])
                    self.depth_width, self.depth_height = self.get_width_height(sample_depth_frame)
                    meta_yaml_data["depth_mode"] = ppc_const.AHAT
                    meta_yaml_data["depth_width"] = self.depth_width
                    meta_yaml_data["depth_height"] = self.depth_height
                elif stream_name == ppc_const.SPATIAL:
                    # 1. Synchronize spatial data
                    spatial_directory = os.path.join(self.data_directory, ppc_const.SPATIAL)
                    synchronized_spatial_directory = os.path.join(self.synchronized_directory, ppc_const.SPATIAL)
                    create_directories(synchronized_spatial_directory)
                    spatial_data_file = f'{self.recording.id}_spatial.pkl'
                    spatial_file_path = os.path.join(spatial_directory, spatial_data_file)
                    sync_spatial_file_path = os.path.join(synchronized_spatial_directory, spatial_data_file)
                    self.create_synchronized_stream_pkl_data(spatial_file_path, sync_spatial_file_path)
                elif stream_name in ppc_const.VLC_LIST:
                    # TODO: Add VLC frame synchronization code
                    logger.log(logging.ERROR, f"Need to implement the VLC Frames Sync Code")
                elif stream_name == ppc_const.IMU_LIST:
                    # 1. Synchronize IMU data
                    imu_directory = os.path.join(self.data_directory, ppc_const.IMU)
                    synchronized_imu_directory = os.path.join(self.synchronized_directory, ppc_const.IMU)
                    create_directories(synchronized_imu_directory)
                    imu_data_file = f'{self.recording.id}_{stream_name}.pkl'
                    imu_file_path = os.path.join(imu_directory, imu_data_file)
                    sync_imu_file_path = os.path.join(synchronized_imu_directory, imu_data_file)
                    self.create_synchronized_stream_pkl_data(imu_file_path, sync_imu_file_path)
                else:
                    logger.log(logging.ERROR, f"Cannot synchronize {stream_name} data with PV as base stream")
                    continue
        elif self.base_stream == ppc_const.DEPTH_AHAT:
            # 1. Create base stream keys used to synchronize the rest of the data
            base_stream_frames_dir = os.path.join(self.base_stream_directory, "depth")
            self.timestamp_to_base_stream_frame = get_timestamp_to_stream_frame(base_stream_frames_dir,
                                                                                stream_extension=".png",
                                                                                timestamp_index=-1)
            self.base_stream_keys = sorted(self.timestamp_to_base_stream_frame.keys())
            self.num_of_frames = len(self.base_stream_keys)
            meta_yaml_data["num_of_frames"] = self.num_of_frames
            synchronized_base_stream_frames_dir = os.path.join(self.synchronized_base_stream_directory, "depth")
            create_directories(synchronized_base_stream_frames_dir)
            sample_base_stream_frame = os.path.join(base_stream_frames_dir, os.listdir(base_stream_frames_dir)[0])
            self.pv_width, self.pv_height = self.get_width_height(sample_base_stream_frame)
            meta_yaml_data["pv_width"] = self.pv_width
            meta_yaml_data["pv_height"] = self.pv_height

            # 2. Copy base stream frames into the synchronized output folder
            for base_stream_counter, base_stream_key in enumerate(self.base_stream_keys):
                src_file = os.path.join(base_stream_frames_dir,
                                        self.timestamp_to_base_stream_frame[base_stream_key])
                dest_file = os.path.join(synchronized_base_stream_frames_dir,
                                         self.depth_stream_suffix % base_stream_counter)
                shutil.copy(src_file, dest_file)
            
            # Synchronize Depth Pose
            depth_ahat_pose_pkl = f'{self.recording.id}_depth_ahat_pose.pkl'
            depth_ahat_pose_file_path = os.path.join(self.base_stream_directory, depth_ahat_pose_pkl)
            sync_depth_ahat_pose_file_path = os.path.join(self.synchronized_base_stream_directory, depth_ahat_pose_pkl)
            self.create_synchronized_stream_pkl_data(depth_ahat_pose_file_path, sync_depth_ahat_pose_file_path)
            
            # 3. Copy the ab frames into the synchronized output folder
            pass

        with open(os.path.join(self.synchronized_directory, "meta.yaml"), "w") as meta_yaml_file:
            for key, value in meta_yaml_data.items():
                meta_yaml_file.write(f"{key}: {value}\n")


def synchronize_data_dir(data_root_dir, rec_instance, base_stream, sync_streams, zipped=False):
    hl2_data_parent_dir = os.path.join(data_root_dir, "hololens")
    go_pro_data_dir = os.path.join(data_root_dir, "gopro")

    hl2_data_recid_dir = os.path.join(hl2_data_parent_dir, rec_instance.id)
    hl2_sync_parent_dir = os.path.join(hl2_data_recid_dir, "sync")
    pv_sync_stream = SynchronizationService(
        base_stream=base_stream,
        synchronize_streams=sync_streams,
        hololens_parent_directory=hl2_data_parent_dir,
        synchronized_data_directory=hl2_sync_parent_dir,
        recording=rec_instance,
    )
    pv_sync_stream.sync_streams()

    if zipped:
        # Compress the data
        cds = CompressDataService(data_dir=hl2_data_recid_dir)
        sync_cds = CompressDataService(data_dir=hl2_sync_parent_dir)
        cds.compress_depth()
        cds.compress_pv()
        sync_cds.compress_depth()
        sync_cds.compress_pv()

        # delete the uncompressed data
        cds.delete_pv_dir()
        cds.delete_depth_dir()
        sync_cds.delete_pv_dir()
        sync_cds.delete_depth_dir()


def test_sync_pv_base():
    base_stream = ppc_const.PHOTOVIDEO
    sync_streams = [
        ppc_const.DEPTH_AHAT, ppc_const.SPATIAL,
        ppc_const.IMU_ACCELEROMETER, ppc_const.IMU_GYROSCOPE, ppc_const.IMU_MAGNETOMETER,
    ]
    # sync_streams = [ppc_const.SPATIAL]
    data_root_dir = "/home/ptg/CODE/data/"
    rec_ids = [
        "4_22",
    ]
    for rec_id in rec_ids:
        rec_instance = Recording(id=rec_id, activity_id=0, is_error=False, steps=[])
        synchronize_data_dir(data_root_dir, rec_instance, base_stream, sync_streams, zipped=False)


if __name__ == '__main__':
    test_sync_pv_base()
