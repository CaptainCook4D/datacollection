import argparse
import os
import time
from pathlib import Path

from open_gopro import WirelessGoPro, Params
from open_gopro.util import add_cli_args_and_parse, setup_logging
from ..utils.logger_config import get_logger

logger = get_logger(__name__)

"""
Open GoPro Python SDK - requires Python >= version 3.9 and < 3.11
Ref: https://gopro.github.io/OpenGoPro/demos/python/sdk_wireless_camera_control
"""


class OpenGoProService:

    def __init__(self, enable_wifi=False, sudo_passwd="ptg@darpa", enable_logging=False) -> None:
        self.enable_wifi = enable_wifi
        self.sudo_password = sudo_passwd
        self.is_recording = False

        if enable_logging:
            parser = argparse.ArgumentParser()
            args = add_cli_args_and_parse(parser, wifi=True)
            self.logger = setup_logging(__name__, args.log)

        self.gopro = WirelessGoPro(enable_wifi=enable_wifi, sudo_password=self.sudo_password)
        self.init_gopro(self.gopro)

    @staticmethod
    def init_gopro(gopro):
        # ToDo: Need to provide GoPro Configuration Settings
        # ToDo: Add Logging
        if not gopro.is_open:
            gopro.open()
        # ToDo: Possible Max Resolution Combinations
        # 1080 - 120 - Super View
        # 1080 - 240 - Wide
        # 4K   - 60  - Wide
        # 5.3K - 30  - Wide
        logger.info("Setting GoPro Configuration Settings")
        gopro.ble_command.load_preset_group(group=Params.PresetGroup.VIDEO)
        gopro.ble_setting.resolution.set(Params.Resolution.RES_4K)
        gopro.ble_setting.fps.set(Params.FPS.FPS_30)
        gopro.ble_setting.video_field_of_view.set(Params.VideoFOV.LINEAR)

        # gopro.ble_setting.video_performance_mode.set(Params.PerformanceMode.MAX_PERFORMANCE)
        gopro.ble_setting.max_lens_mode.set(Params.MaxLensMode.DEFAULT)
        gopro.ble_setting.camera_ux_mode.set(Params.CameraUxMode.PRO)
        gopro.ble_command.set_turbo_mode(mode=Params.Toggle.DISABLE)
        assert gopro.ble_command.load_preset_group(group=Params.PresetGroup.VIDEO).is_ok

    def start_recording(self):
        self.close_wifi_connection()
        if self.is_recording:
            logger.info("Recording is in progress")
            return
        self.gopro.ble_command.set_shutter(shutter=Params.Toggle.ENABLE)
        # self.gopro.http_command.set_shutter(shutter=Params.Toggle.ENABLE)
        logger.info("Recording Started")
        self.is_recording = True

    def stop_recording(self, folder_path, file_name):
        if not self.is_recording:
            logger.info("Recording is in progress")
            return
        self.gopro.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
        # self.gopro.http_command.set_shutter(shutter=Params.Toggle.DISABLE)
        logger.info("Recording Stopped")
        self.is_recording = False
        
        self.download_most_recent_video(folder_path, file_name + ".MP4")

    def download_videos(self, folder_path):
        self.open_wifi_connection()
        media_list = [x["n"] for x in self.gopro.http_command.get_media_list().flatten]
        media_list = sorted(media_list)
        for file in media_list:
            local_file = os.path.abspath(os.path.join(folder_path, file))
            local_path = Path(local_file)
            self.gopro.http_command.download_file(camera_file=file, local_file=local_path)
        self.close_wifi_connection()

    def close_all_connections(self):
        self.gopro.close()

    def open_wifi_connection(self):
        if not self.gopro.is_open or self.enable_wifi:
            return
        self.enable_wifi = True
        self.gopro.close()
        self.gopro = WirelessGoPro(enable_wifi=True, sudo_password=self.sudo_password)
        self.gopro.open()

    def close_wifi_connection(self):
        if not self.gopro.is_open or not self.enable_wifi:
            return
        self.enable_wifi = False
        self.gopro.close()
        self.gopro = WirelessGoPro(enable_wifi=False, sudo_password=self.sudo_password)
        self.gopro.open()

    def download_most_recent_video(self, folder_path, file_name=None):
        # The video (is most likely) the difference between the two sets
        # recent_video = self.media_set_after.difference(self.media_set_before).pop()
        logger.info("Downloading Most Recent Video by opening WiFi Connection")
        self.open_wifi_connection()
        media_list = [x["n"] for x in self.gopro.http_command.get_media_list().flatten]
        recent_video = sorted(media_list)[-1]
        if file_name is not None:
            local_file = os.path.abspath(os.path.join(folder_path, file_name))
        else:
            local_file = os.path.abspath(os.path.join(folder_path, recent_video))
        local_path = Path(local_file)

        self.gopro.http_command.download_file(camera_file=recent_video, local_file=local_path)
        self.close_wifi_connection()
        logger.info("Downloaded Most Recent Video and closed WiFi Connection")

    def get_video_preview(self):
        self.open_wifi_connection()
        media_list = [x["n"] for x in self.gopro.http_command.get_media_list().flatten]
        recent_video = sorted(media_list)[-1]
        self.gopro.http_command.get_preview(camera_file=recent_video)
        self.close_wifi_connection()


def test_record_video():
    TIME = 2.0
    MINUTES = 10.0
    RECORD = False

    gopro = OpenGoProService(enable_wifi=False, enable_logging=False)

    # if RECORD:
    #     gopro.start_recording()
    #     time.sleep(TIME * MINUTES)
    #     gopro.stop_recording()

    gopro_videos_dir = "../../../../../gopro_videos"
    if not os.path.exists(gopro_videos_dir):
        os.makedirs(gopro_videos_dir)
    gopro.download_most_recent_video(gopro_videos_dir)

    # gopro.close_all_connections()


if __name__ == '__main__':
    test_record_video()
