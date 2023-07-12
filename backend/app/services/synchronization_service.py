import os
import pickle
import shutil
import time
import zipfile
from typing import List

import cv2

from ..hololens import hl2ss
from ..models.recording import Recording
from ..post_processing.compress_data_service import CompressDataService
from ..utils.constants import Synchronization_Constants as const
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


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


def get_ts_to_stream_frame(
        stream_directory,
        stream_extension,
        ts_index=-1
):
    stream_extension_length = len(stream_extension)
    stream_frames = [frame for frame in os.listdir(stream_directory) if frame.endswith(stream_extension)]
    
    def get_ts_from_stream_file_name(stream_file_name):
        _splits = (stream_file_name[:-stream_extension_length].split("_"))
        if _splits[ts_index] == "depth" or _splits[ts_index] == "ab":
            return int(_splits[ts_index - 1])
        return int(_splits[ts_index])
    
    stream_frames = sorted(stream_frames, key=lambda x: get_ts_from_stream_file_name(x))
    
    ts_to_stream_frame = {}
    for stream_frame in stream_frames:
        ts = get_ts_from_stream_file_name(stream_frame)
        ts_to_stream_frame[ts] = stream_frame
    
    return ts_to_stream_frame


def count_files_in_directory(directory):
    file_count = 0
    for root, dirs, files in os.walk(directory):
        file_count += len(files)
    return file_count


def directories_have_same_file_count(dir1, dir2):
    count1 = count_files_in_directory(dir1)
    logger.info(f"dir1: {dir1} has {count1} files")
    count2 = count_files_in_directory(dir2)
    logger.info(f"dir2: {dir2} has {count2} files")
    return count1 == count2


def files_have_same_size(file1, file2):
    if not os.path.exists(file1) or not os.path.exists(file2):
        return False
    return os.path.getsize(file1) == os.path.getsize(file2)


def is_zip_extracted(zip_file_path, extract_dir):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
        # Get the list of files in the ZIP archive
        zip_file_list = zip_file.namelist()
    
    # Get the list of files in the extraction directory
    extracted_files = []
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            extracted_files.append(os.path.join(root, file))
    
    # Compare the lists and check if they are the same
    return sorted(zip_file_list) == sorted(extracted_files)


def extract_zip_file(zip_file_path, output_directory, recording_id):
    if os.path.exists(output_directory):
        logger.info(f"[{recording_id}] Zip file already extracted")
        return
    
    logger.info(f"[{recording_id}] Extracting zip file: {zip_file_path}")
    start_time = time.time()
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(output_directory)
    extraction_time = time.time() - start_time
    extraction_time_readable = time.strftime("%H:%M:%S", time.gmtime(extraction_time))
    logger.info(f"[{recording_id}] Extracting zip file took: {extraction_time_readable}")


def make_video(images_folder, video_name, recording_id):
    images = [img for img in os.listdir(images_folder) if img.endswith(".jpg")]
    images = sorted(images, key=lambda x: int((x[:-4].split("-"))[-1]))
    
    frame = cv2.imread(os.path.join(images_folder, images[0]))
    height, width, layers = frame.shape
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    # video = cv2.VideoWriter(video_name, 0, 30, (width, height))
    video = cv2.VideoWriter(video_name, fourcc, 30, (width, height))
    
    start_time = time.time()
    for image in images:
        video.write(cv2.imread(os.path.join(images_folder, image)))
    
    cv2.destroyAllWindows()
    video.release()
    
    video_creation_time = time.time() - start_time
    video_creation_time_readable = time.strftime("%H:%M:%S", time.gmtime(video_creation_time))
    logger.info(f"[{recording_id}] Video creation took: {video_creation_time_readable}")


class SynchronizationServiceV2:
    
    def __init__(
            self,
            data_parent_directory: str,
            recording: Recording,
            base_stream: str,
            synchronize_streams: List[str],
    ):
        self.base_stream = base_stream
        self.synchronize_streams = synchronize_streams
        self.recording = recording
        self.recording_id = self.recording.get_recording_id()
        self.data_recording_directory = os.path.join(data_parent_directory, self.recording_id)
        
        self.raw_data_directory = os.path.join(self.data_recording_directory, const.RAW)
        self.sync_data_directory = os.path.join(self.data_recording_directory, const.SYNC)
        create_directories(self.sync_data_directory)
        
        self.raw_hololens_info_file = os.path.join(self.raw_data_directory, const.HOLOLENS_INFO_FILE_NAME)
        
        self.raw_base_stream_directory = os.path.join(self.raw_data_directory, self.base_stream)
        self.sync_base_stream_directory = os.path.join(self.sync_data_directory, self.base_stream)
        
        self.ts_to_base_stream_frame = None
        self.base_stream_keys = None
        
        self.pv_stream_suffix = "color-%06d.jpg"
        self.depth_stream_suffix = "depth-%06d.png"
        self.ab_stream_suffix = "ab-%06d.png"
        
        self.num_of_frames = 0
        self.depth_mode = None
        self.depth_width = None
        self.depth_height = None
        self.pv_width = None
        self.pv_height = None
        self.meta_yaml_data = {}
        
        self.device_id = self._get_device_id()
    
    def is_synchronizable(self):
        if not os.path.exists(self.raw_base_stream_directory):
            return False
        return True
    
    def _get_device_id(self):
        with open(self.raw_hololens_info_file, 'r') as f:
            hololens_info_data = f.readlines()
        for line in hololens_info_data:
            if line.startswith("Hololens2 Name"):
                return line.split(":")[1].strip()
    
    def get_image_characteristics(self, image_path):
        image = cv2.imread(image_path)
        return image.shape[1], image.shape[0]
    
    def get_ts_pkl_frame_map(self, stream_pkl_file_path):
        ts_to_stream_payload = {}
        pkl_frames = read_stream_pkl_data(stream_pkl_file_path)
        for pkl_frame in pkl_frames:
            ts, payload = pkl_frame if type(pkl_frame) is tuple else (pkl_frame.ts, pkl_frame.payload)
            if type(payload) is bytearray:
                payload = hl2ss.unpack_si(payload)
            ts_to_stream_payload[ts] = payload
        return ts_to_stream_payload
    
    def create_sync_stream_pkl_data(self, stream_pkl_file_path, sync_stream_output_directory, base_ts_to_stream_ts):
        # 1. Load pickle file data into a dictionary
        ts_to_stream_payload = self.get_ts_pkl_frame_map(stream_pkl_file_path)
        
        # 2. Use the base_stream_keys and loaded pickle file data to synchronize them
        synced_ts_to_stream_payload = {}
        for base_stream_counter, base_stream_key in enumerate(self.base_stream_keys):
            if base_stream_key not in base_ts_to_stream_ts or base_ts_to_stream_ts[base_stream_key] is None:
                logger.info(f"[{self.recording_id}] Skipping pkl frame %s" % base_stream_key)
                continue
            stream_ts = base_ts_to_stream_ts[base_stream_key]
            stream_payload = ts_to_stream_payload[stream_ts]
            synced_ts_to_stream_payload[base_stream_counter] = (stream_ts, stream_payload)
        write_pickle_data(synced_ts_to_stream_payload, sync_stream_output_directory)
        
    def create_sync_pv_stream_pkl_data(self, stream_pkl_file_path, sync_stream_output_path):
        # 1. Load pickle file data into a dictionary
        ts_to_stream_payload = self.get_ts_pkl_frame_map(stream_pkl_file_path)
        
        # 2. Use the base_stream_keys and loaded pickle file data to synchronize them
        synced_ts_to_stream_payload = {}
        for base_stream_counter, base_stream_key in enumerate(self.base_stream_keys):
            if base_stream_key not in ts_to_stream_payload or ts_to_stream_payload[base_stream_key] is None:
                logger.info(f"[{self.recording_id}] Skipping pkl frame %s" % base_stream_key)
                continue
            stream_ts = base_stream_key
            stream_payload = ts_to_stream_payload[stream_ts]
            synced_ts_to_stream_payload[base_stream_counter] = (stream_ts, stream_payload)
        write_pickle_data(synced_ts_to_stream_payload, sync_stream_output_path)
    
    def create_sync_stream_frames(
            self,
            raw_stream_directory,
            stream_extension,
            sync_stream_output_directory,
            stream_suffix,
            base_ts_to_stream_ts
    ):
        ts_to_stream_frame = get_ts_to_stream_frame(raw_stream_directory, stream_extension)
        for base_stream_counter, base_stream_key in enumerate(self.base_stream_keys):
            if base_stream_key not in base_ts_to_stream_ts or base_ts_to_stream_ts[base_stream_key] is None:
                logger.info(f"[{self.recording_id}] Skipping frame %s" % base_stream_key)
                continue
            stream_ts = base_ts_to_stream_ts[base_stream_key]
            shutil.copy(
                os.path.join(raw_stream_directory, ts_to_stream_frame[stream_ts]),
                os.path.join(sync_stream_output_directory, stream_suffix % base_stream_counter)
            )
        return
    
    def get_stream_keys_from_dir(self, stream_directory, stream_extension, ts_index):
        ts_to_stream_frame = get_ts_to_stream_frame(stream_directory, stream_extension, ts_index)
        return list(ts_to_stream_frame.keys())
    
    def get_stream_keys_from_pkl(self, pkl_file_path):
        ts_to_stream_frame_pkl = self.get_ts_pkl_frame_map(pkl_file_path)
        return list(ts_to_stream_frame_pkl.keys())
    
    def create_base_ts_to_stream_ts_map(self, stream_keys):
        base_ts_to_stream_ts = {}
        base_idx_to_stream_idx = {}
        
        for base_stream_counter, base_stream_key in enumerate(self.base_stream_keys):
            stream_ts_idx = 0 if base_stream_counter == 0 else base_idx_to_stream_idx[base_stream_counter - 1]
            best_base_ts_stream_ts_distance = abs(base_stream_key - stream_keys[stream_ts_idx])
            
            while stream_ts_idx < len(stream_keys) and abs(
                    base_stream_key - stream_keys[stream_ts_idx]) <= best_base_ts_stream_ts_distance:
                best_base_ts_stream_ts_distance = abs(base_stream_key - stream_keys[stream_ts_idx])
                stream_ts_idx += 1
            
            stream_ts_idx -= 1
            stream_ts = stream_keys[stream_ts_idx]
            logger.debug(
                f"[{self.recording_id}] Base Stream Key: %d, Stream Timestamp: %d" % (base_stream_key, stream_ts))
            base_idx_to_stream_idx[base_stream_counter] = stream_ts_idx
            
            if abs(base_stream_key - stream_ts) > 1e8:
                logger.error(
                    f"[{self.recording_id}] Difference between base stream key and stream timestamp is greater than 1 second")
                base_ts_to_stream_ts[base_stream_key] = None
            else:
                base_ts_to_stream_ts[base_stream_key] = stream_ts
        
        return base_ts_to_stream_ts
    
    def sync_streams(self):
        if not self.is_synchronizable():
            logger.info(f"[{self.recording_id}] Cannot synchronize streams")
            return
        
        # meta.yaml file data
        self.meta_yaml_data["device_id"] = self.device_id
        # 1. Create base stream keys used to synchronize the rest of the data
        frames_zip_file_path = os.path.join(self.raw_base_stream_directory, const.FRAMES_ZIP)
        raw_base_stream_frames_dir = os.path.join(self.raw_base_stream_directory, const.FRAMES)
        if os.path.exists(frames_zip_file_path):
            extract_zip_file(frames_zip_file_path, raw_base_stream_frames_dir, self.recording_id)
        
        self.ts_to_base_stream_frame = get_ts_to_stream_frame(raw_base_stream_frames_dir, const.JPEG_EXTENSION, -1)
        self.base_stream_keys = sorted(self.ts_to_base_stream_frame.keys())
        self.num_of_frames = len(self.base_stream_keys)
        self.meta_yaml_data["num_of_frames"] = self.num_of_frames
        
        sample_base_stream_frame_path = os.path.join(
            raw_base_stream_frames_dir,
            os.listdir(raw_base_stream_frames_dir)[0]
        )
        
        self.pv_width, self.pv_height = self.get_image_characteristics(sample_base_stream_frame_path)
        self.meta_yaml_data["pv_width"] = self.pv_width
        self.meta_yaml_data["pv_height"] = self.pv_height
        
        sync_base_stream_frames_dir = os.path.join(self.sync_base_stream_directory, const.FRAMES)
        
        # 2. Copy base stream frames into the sync output folder
        if not os.path.exists(sync_base_stream_frames_dir):
            create_directories(sync_base_stream_frames_dir)
            logger.info(f"[{self.recording_id}] Copying base stream frames into the sync output folder")
            start_base_stream_time = time.time()
            for base_stream_counter, base_stream_key in enumerate(self.base_stream_keys):
                src_file = os.path.join(raw_base_stream_frames_dir, self.ts_to_base_stream_frame[base_stream_key])
                dest_file = os.path.join(sync_base_stream_frames_dir, self.pv_stream_suffix % base_stream_counter)
                shutil.copy(src_file, dest_file)
            end_base_stream_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - start_base_stream_time))
            logger.info(
                f"[{self.recording_id}] Done copying base stream frames into the sync output folder : {end_base_stream_time}")
        else:
            logger.info(f"[{self.recording_id}] Skipping copying base stream frames into the sync output folder")
        
        # Synchronize PV Pose
        pv_pose_pkl = f'{self.recording.id}_pv_pose.pkl'
        raw_pv_pose_file_path = os.path.join(self.raw_base_stream_directory, pv_pose_pkl)
        sync_pv_pose_file_path = os.path.join(self.sync_base_stream_directory, pv_pose_pkl)
        
        if not os.path.exists(sync_pv_pose_file_path):
            logger.info(f"[{self.recording_id}] Copying PV Pose into the sync output folder")
            start_pv_pose_time = time.time()
            self.create_sync_pv_stream_pkl_data(raw_pv_pose_file_path, sync_pv_pose_file_path)
            end_pv_pose_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - start_pv_pose_time))
            logger.info(f"[{self.recording_id}] Done copying PV Pose into the sync output folder : {end_pv_pose_time}")
        else:
            logger.info(f"[{self.recording_id}] Skipping copying PV Pose into the sync output folder")
        
        recording_base_stream_mp4_file_path = os.path.join(self.sync_base_stream_directory, f"{self.recording.id}.mp4")
        if not os.path.exists(recording_base_stream_mp4_file_path):
            logger.info(f"[{self.recording_id}] Recording base stream mp4 file does not exist")
            logger.info(f"[{self.recording_id}] Creating recording base stream mp4 file")
            make_video(raw_base_stream_frames_dir, recording_base_stream_mp4_file_path, self.recording_id)
            logger.info(f"[{self.recording_id}] Done creating recording base stream mp4 file")
        else:
            logger.info(f"[{self.recording_id}] Skipping creation of recording base stream mp4 file")
        
        for stream_name in self.synchronize_streams:
            if stream_name == const.DEPTH_AHAT:
                # Files and directories
                raw_depth_parent_directory = os.path.join(self.raw_data_directory, const.DEPTH_AHAT)
                sync_depth_parent_directory = os.path.join(self.sync_data_directory, const.DEPTH_AHAT)
                create_directories(sync_depth_parent_directory)
                
                depth_ahat_pkl = f'{self.recording.id}_depth_ahat_pose.pkl'
                raw_depth_pose_file_path = os.path.join(raw_depth_parent_directory, depth_ahat_pkl)
                sync_depth_pose_file_path = os.path.join(sync_depth_parent_directory, depth_ahat_pkl)
                
                raw_depth_data_directory = os.path.join(raw_depth_parent_directory, const.DEPTH)
                raw_depth_frames_zip_file_path = os.path.join(raw_depth_parent_directory, const.DEPTH_ZIP)
                if os.path.exists(raw_depth_frames_zip_file_path) and not os.path.exists(raw_depth_data_directory):
                    logger.info(f"[{self.recording_id}] Extracting depth frames zip file")
                    extract_zip_file(raw_depth_frames_zip_file_path, raw_depth_data_directory, self.recording_id)
                    logger.info(f"[{self.recording_id}] Done extracting depth frames zip file")
                else:
                    logger.info(f"[{self.recording_id}] Skipping extracting depth frames zip file")
                
                sync_depth_data_directory = os.path.join(sync_depth_parent_directory, const.DEPTH)
                
                raw_depth_ab_directory = os.path.join(raw_depth_parent_directory, const.AB)
                raw_ab_frames_zip_file_path = os.path.join(raw_depth_parent_directory, const.AB_ZIP)
                if os.path.exists(raw_depth_frames_zip_file_path) and not os.path.exists(raw_depth_ab_directory):
                    logger.info(f"[{self.recording_id}] Extracting ab frames zip file")
                    extract_zip_file(raw_ab_frames_zip_file_path, raw_depth_ab_directory, self.recording_id)
                    logger.info(f"[{self.recording_id}] Done extracting ab frames zip file")
                else:
                    logger.info(f"[{self.recording_id}] Skipping extracting ab frames zip file")
                
                sync_depth_ab_directory = os.path.join(sync_depth_parent_directory, const.AB)
                
                # 0. Create base stream timestamp - synchronize stream timestamp mapping
                stream_keys = self.get_stream_keys_from_dir(raw_depth_data_directory, const.PNG_EXTENSION, -1)
                base_ts_to_stream_ts = self.create_base_ts_to_stream_ts_map(stream_keys)
                
                # if os.path.exists(sync_depth_pose_file_path):
                #     logger.info(f"[{self.recording_id}] Synchronized Depth Pose data already exists")
                #     logger.info(f"[{self.recording_id}] Removing existing Synchronized Depth Pose data {sync_depth_pose_file_path}")
                #     os.remove(sync_depth_pose_file_path)
                
                if not os.path.exists(sync_depth_pose_file_path):
                    # 1. Synchronize Pose
                    logger.info(f"[{self.recording_id}] Synchronizing Depth Pose data")
                    start_depth_pose_time = time.time()
                    self.create_sync_stream_pkl_data(
                        raw_depth_pose_file_path,
                        sync_depth_pose_file_path,
                        base_ts_to_stream_ts
                    )
                    total_depth_pose_time = time.strftime(
                        "%H:%M:%S",
                        time.gmtime(time.time() - start_depth_pose_time)
                    )
                    logger.info(f"[{self.recording_id}] Done synchronizing Depth Pose data : {total_depth_pose_time}")
                else:
                    logger.info(f"[{self.recording_id}] Skipping synchronizing Depth Pose data")
                
                if not os.path.exists(sync_depth_data_directory):
                    create_directories(sync_depth_data_directory)
                    # 2. Synchronize Depth data
                    logger.info(f"[{self.recording_id}] Synchronizing Depth data")
                    start_depth_time = time.time()
                    self.create_sync_stream_frames(
                        raw_depth_data_directory,
                        const.PNG_EXTENSION,
                        sync_depth_data_directory,
                        self.depth_stream_suffix,
                        base_ts_to_stream_ts
                    )
                    total_depth_time = time.strftime(
                        "%H:%M:%S",
                        time.gmtime(time.time() - start_depth_time)
                    )
                    logger.info(f"[{self.recording_id}] Done synchronizing Depth data : {total_depth_time}")
                else:
                    logger.info(f"[{self.recording_id}] Skipping synchronizing Depth data")
                
                if not os.path.exists(sync_depth_ab_directory):
                    create_directories(sync_depth_ab_directory)
                    # 3. Synchronize Active Brightness data
                    logger.info(f"[{self.recording_id}] Synchronizing Active Brightness data")
                    start_ab_time = time.time()
                    self.create_sync_stream_frames(
                        raw_depth_ab_directory,
                        const.PNG_EXTENSION,
                        sync_depth_ab_directory,
                        self.ab_stream_suffix,
                        base_ts_to_stream_ts
                    )
                    total_ab_time = time.strftime(
                        "%H:%M:%S",
                        time.gmtime(time.time() - start_ab_time)
                    )
                    logger.info(f"[{self.recording_id}] Done synchronizing Active Brightness data : {total_ab_time}")
                else:
                    logger.info(f"[{self.recording_id}] Skipping synchronizing Active Brightness data")
                
                sample_depth_frame = os.path.join(raw_depth_data_directory, os.listdir(raw_depth_data_directory)[0])
                self.depth_width, self.depth_height = self.get_image_characteristics(sample_depth_frame)
                self.meta_yaml_data["depth_mode"] = const.AHAT
                self.meta_yaml_data["depth_width"] = self.depth_width
                self.meta_yaml_data["depth_height"] = self.depth_height
            
                # 4. Compress all frames into a zip file in both raw and sync directories
                # sync_depth_frames_zip_file_path = os.path.join(sync_depth_parent_directory, const.DEPTH_ZIP)
                # if not os.path.exists(sync_depth_frames_zip_file_path):
                #     logger.info(f"[{self.recording_id}] Compressing Depth data")
                #     start_compress_depth_time = time.time()
                #     CompressDataService.compress_dir(sync_depth_parent_directory, const.DEPTH)
                #     total_compress_depth_time = time.strftime(
                #         "%H:%M:%S",
                #         time.gmtime(time.time() - start_compress_depth_time)
                #     )
                #     logger.info(f"[{self.recording_id}] Done compressing Depth data : {total_compress_depth_time}")
                # else:
                #     logger.info(f"[{self.recording_id}] Skipping compressing Depth data")
                #
                # sync_depth_ab_frames_zip_file_path = os.path.join(sync_depth_parent_directory, const.AB_ZIP)
                # if not os.path.exists(sync_depth_ab_frames_zip_file_path):
                #     logger.info(f"[{self.recording_id}] Compressing Active Brightness data")
                #     start_compress_ab_time = time.time()
                #     CompressDataService.compress_dir(sync_depth_parent_directory, const.AB)
                #     total_compress_ab_time = time.strftime(
                #         "%H:%M:%S",
                #         time.gmtime(time.time() - start_compress_ab_time)
                #     )
                #     logger.info(f"[{self.recording_id}] Done compressing Active Brightness data : {total_compress_ab_time}")
                # else:
                #     logger.info(f"[{self.recording_id}] Skipping compressing Active Brightness data")
            
            # # 5. Delete raw frames directory
            # logger.info("Deleting frames directory")
            # CompressDataService.delete_dir(raw_depth_data_directory)
            # CompressDataService.delete_dir(sync_depth_data_directory)
            # logger.info("Done deleting raw frames directory")
            # logger.info("Deleting ab directory")
            # CompressDataService.delete_dir(raw_depth_ab_directory)
            # CompressDataService.delete_dir(sync_depth_ab_directory)
            # logger.info("Done deleting ab directory")
            elif stream_name == const.SPATIAL:
                # 1. Synchronize spatial data
                spatial_directory = os.path.join(self.raw_data_directory, const.SPATIAL)
                sync_spatial_directory = os.path.join(self.sync_data_directory, const.SPATIAL)
                create_directories(sync_spatial_directory)
                
                spatial_data_file = f'{self.recording.id}_spatial.pkl'
                spatial_file_path = os.path.join(spatial_directory, spatial_data_file)
                sync_spatial_file_path = os.path.join(sync_spatial_directory, spatial_data_file)
                
                stream_keys = self.get_stream_keys_from_pkl(spatial_file_path)
                base_ts_to_stream_ts = self.create_base_ts_to_stream_ts_map(stream_keys)
                
                # if os.path.exists(sync_spatial_file_path):
                #     logger.info(f"[{self.recording_id}] Synchronized Spatial data already exists")
                #     logger.info(f"[{self.recording_id}] Deleting existing synchronized Spatial data {sync_spatial_file_path}")
                #     os.remove(sync_spatial_file_path)
                
                if not os.path.exists(sync_spatial_file_path):
                    logger.info(f"[{self.recording_id}] Synchronizing Spatial data")
                    start_spatial_time = time.time()
                    self.create_sync_stream_pkl_data(spatial_file_path, sync_spatial_file_path, base_ts_to_stream_ts)
                    total_spatial_time = time.strftime(
                        "%H:%M:%S",
                        time.gmtime(time.time() - start_spatial_time)
                    )
                    logger.info(f"[{self.recording_id}] Done synchronizing Spatial data : {total_spatial_time}")
                else:
                    logger.info(f"[{self.recording_id}] Skipping synchronizing Spatial data")
                    
            elif stream_name in const.IMU_LIST:
                imu_directory = os.path.join(self.raw_data_directory, const.IMU)
                sync_imu_directory = os.path.join(self.sync_data_directory, const.IMU)
                create_directories(sync_imu_directory)
                
                imu_data_file = f'{self.recording.id}_{stream_name}.pkl'
                imu_file_path = os.path.join(imu_directory, imu_data_file)
                sync_imu_file_path = os.path.join(sync_imu_directory, imu_data_file)
                
                stream_keys = self.get_stream_keys_from_pkl(imu_file_path)
                base_ts_to_stream_ts = self.create_base_ts_to_stream_ts_map(stream_keys)
                
                # if os.path.exists(sync_imu_file_path):
                #     logger.info(f"[{self.recording_id}] Synchronized {stream_name} data already exists")
                #     logger.info(f"[{self.recording_id}] Deleting existing synchronized {stream_name} data {sync_imu_file_path}")
                #     os.remove(sync_imu_file_path)
                
                if not os.path.exists(sync_imu_file_path):
                    logger.info(f"[{self.recording_id}] Synchronizing {stream_name} data")
                    start_imu_time = time.time()
                    self.create_sync_stream_pkl_data(imu_file_path, sync_imu_file_path, base_ts_to_stream_ts)
                    total_imu_time = time.strftime(
                        "%H:%M:%S",
                        time.gmtime(time.time() - start_imu_time)
                    )
                    logger.info(f"[{self.recording_id}] Done synchronizing {stream_name} data : {total_imu_time}")
                else:
                    logger.info(f"[{self.recording_id}] Skipping synchronizing {stream_name} data")
        
        # sync_pv_frames_zip_file_path = os.path.join(self.sync_base_stream_directory, const.FRAMES_ZIP)
        # if not os.path.exists(sync_pv_frames_zip_file_path):
        #     logger.info(f"[{self.recording_id}] Compressing pv frames directory")
        #     start_compress_pv_time = time.time()
        #     CompressDataService.compress_dir(self.sync_base_stream_directory, const.FRAMES)
        #     total_compress_pv_time = time.strftime(
        #         "%H:%M:%S",
        #         time.gmtime(time.time() - start_compress_pv_time)
        #     )
        #     logger.info(f"[{self.recording_id}] Done compressing pv frames directory : {total_compress_pv_time}")
        # else:
        #     logger.info(f"[{self.recording_id}] Skipping compressing pv frames directory")
        
        # # Delete raw frames directory
        # logger.info("Deleting pv frames directory")
        # CompressDataService.delete_dir(raw_base_stream_frames_dir)
        # CompressDataService.delete_dir(sync_base_stream_frames_dir)
        # logger.info("Done deleting pv frames directory")
        
        # with open(os.path.join(self.sync_data_directory, "meta.yaml"), "w") as meta_yaml_file:
        #     for key, value in self.meta_yaml_data.items():
        #         meta_yaml_file.write(f"{key}: {value}\n")
