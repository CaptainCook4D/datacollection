import os
import threading
import time

from datacollection.user_app.backend.app.models.recording import Recording
from datacollection.user_app.backend.app.services.hololens_service import HololensService


def record_all_streams(hololens_service: HololensService, recording: Recording, hololens_dir):
    rec_thread = threading.Thread(target=hololens_service.start_recording, args=(recording, hololens_dir))
    rec_thread.start()

    print("Recording Started")
    sleep_time_in_mins = 1
    for min_done in range(sleep_time_in_mins):
        print("Minutes done {}".format(min_done))
        time.sleep(60.0 * sleep_time_in_mins)
    # hl2_stop_thread = threading.Thread(target=hololens_service.stop_recording)
    # hl2_stop_thread.start()
    print("Recording Stopping")
    hololens_service.stop_recording()
    print("Recording Stopped")

    rec_thread.join()
    # hl2_stop_thread.join()


if __name__ == '__main__':
    ip_address = '192.168.1.152'
    data_dir = "/home/ptg/CODE/data/"
    rec_id = "4_22"
    hl2_service = HololensService()
    hololens_dir = os.path.join(data_dir, "hololens")
    rec_instance = Recording(id=rec_id, activity_id=0, is_error=False, steps=[])
    record_all_streams(hl2_service, rec_instance, hololens_dir)
