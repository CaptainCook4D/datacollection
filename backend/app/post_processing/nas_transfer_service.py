import os
import time

import pysftp
from ..utils.constants import Post_Processing_Constants as const
from ..models.recording import Recording
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class NASTransferService:

    def __init__(self, recording, local_data_root_dir: str):
        self.recording = recording
        self.local_data_root_dir = local_data_root_dir
        self.remote_data_root_dir = const.NAS_DATA_ROOT_DIR

    def _transfer_directory(self, sftp_client, src_directory, dst_directory, is_file=False):
        if not is_file:
            sftp_client.makedirs(dst_directory)
        for item in os.listdir(src_directory):
            src_path = os.path.join(src_directory, item)
            dst_path = os.path.join(dst_directory, item)
            if os.path.isfile(src_path) or is_file:
                try:
                    sftp_client.stat(dst_path)
                    logger.info(f"File {dst_path} already exists on NAS. Skipping transfer.")
                    continue
                except FileNotFoundError:
                    logger.info(f"File {dst_path} does not exist on NAS. Transferring...")
                sftp_client.put(src_path, dst_path)
                logger.info(f'Transferred {item} to NAS')
            elif os.path.isdir(src_path):
                self._transfer_directory(sftp_client, src_path, dst_path)

    def _timed_transfer_to_nas(self, sftp_client, node_name, directory_path, remote_node_path, is_file=False):
        start_time = time.time()
        logger.info(f"[BEGIN] Transfer to NAS {node_name} for recording {self.recording.id}")
        if is_file:
            remote_file_path = os.path.join(remote_node_path, node_name)
            try:
                sftp_client.stat(remote_file_path)
                logger.info(f"File {remote_file_path} already exists on NAS. Skipping transfer.")
                return
            except FileNotFoundError:
                logger.info(f"File {remote_file_path} does not exist on NAS. Transferring...")
            sftp_client.put(directory_path, remote_file_path)
        else:
            self._transfer_directory(sftp_client, directory_path, remote_node_path)
        end_time = time.time()
        logger.info(
            f"[END] Transfer to NAS {node_name} in {end_time - start_time} seconds for recording {self.recording.id}")

    def transfer_from_local_to_nas(self):
        sftp_client = pysftp.Connection(const.NAS_HOST_IP, username=const.NAS_USERNAME, password=const.NAS_PASSWORD)
        # sftp_client.cd(self.remote_data_root_dir)
        remote_recording_directory = os.path.join(self.remote_data_root_dir, self.recording.id)
        # mkdir_p(sftp_client, remote_recording_directory)
        try:
            sftp_client.stat(remote_recording_directory)
        except FileNotFoundError:
            sftp_client.mkdir(remote_recording_directory)
        sftp_client.chdir(remote_recording_directory)

        remote_hl2_raw_data_dir = os.path.join(remote_recording_directory, const.RAW)
        try:
            sftp_client.stat(remote_hl2_raw_data_dir)
        except FileNotFoundError:
            sftp_client.mkdir(remote_hl2_raw_data_dir)

        remote_hl2_sync_data_dir = os.path.join(remote_recording_directory, const.SYNC)
        try:
            sftp_client.stat(remote_hl2_sync_data_dir)
        except FileNotFoundError:
            sftp_client.mkdir(remote_hl2_sync_data_dir)

        remote_hl2_gopro_data_dir = os.path.join(remote_recording_directory, const.GOPRO)
        try:
            sftp_client.stat(remote_hl2_gopro_data_dir)
        except FileNotFoundError:
            sftp_client.mkdir(remote_hl2_gopro_data_dir)

        local_hl2_root_dir = os.path.join(self.local_data_root_dir, 'hololens')
        local_hl2_data_dir = os.path.join(local_hl2_root_dir, self.recording.id)

        # 1. Transfer RAW data to NAS
        for node in os.listdir(local_hl2_data_dir):
            node_path = os.path.join(local_hl2_data_dir, node)
            if os.path.isdir(node_path) and node not in (const.SYNC, const.GOPRO):
                remote_node_path = os.path.join(remote_hl2_raw_data_dir, node)
                self._timed_transfer_to_nas(sftp_client, node, node_path, remote_node_path)

        # # 2. Transfer Synchronized data to NAS
        # local_hl2_sync_data_dir = os.path.join(local_hl2_data_dir, const.SYNC)
        # self._timed_transfer_to_nas(sftp_client, const.SYNC, local_hl2_sync_data_dir, remote_hl2_sync_data_dir)

        # 3. Transfer GOPRO data to NAS
        # local_go_pro_file = os.path.join(self.local_data_root_dir, const.GOPRO, self.recording.id + '.MP4')
        # self._timed_transfer_to_nas(sftp_client, self.recording.id + '.MP4', local_go_pro_file,
        #                             remote_hl2_gopro_data_dir, is_file=True)
        #
        # local_go_pro_360p_file = os.path.join(self.local_data_root_dir, const.GOPRO_360P,
        #                                       self.recording.id + '_360p.mp4')
        # self._timed_transfer_to_nas(sftp_client, self.recording.id + '_360p.mp4', local_go_pro_360p_file,
        #                             remote_hl2_gopro_data_dir, is_file=True)

        sftp_client.close()

    def transfer_from_nas_to_box(self):
        pass


def test_nas_transfer_service():
    # mocking the recording instance
    rec_id = '9_15'
    rec_instance = Recording(id=rec_id, activity_id=9, is_error=False, steps=[])
    data_dir = "../../../../../../data/"

    nas_transfer_service = NASTransferService(rec_instance, data_dir)
    nas_transfer_service.transfer_from_local_to_nas()


if __name__ == '__main__':
    test_nas_transfer_service()
