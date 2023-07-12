import os

from datacollection.user_app.backend.app.services.open_gopro_service import OpenGoProService


def test_record_video():
    TIME = 2.0
    MINUTES = 10.0
    RECORD = False

    gopro = OpenGoProService(enable_wifi=False, enable_logging=False)

    # if RECORD:
    #     gopro.start_recording()
    #     time.sleep(TIME * MINUTES)
    #     gopro.stop_recording()

    gopro_videos_dir = "../../../../gopro_videos"
    if not os.path.exists(gopro_videos_dir):
        os.makedirs(gopro_videos_dir)
    gopro.download_most_recent_video(gopro_videos_dir)


if __name__ == '__main__':
    test_record_video()
