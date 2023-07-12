from datacollection.user_app.backend.app.models.recording import Recording
from datacollection.user_app.backend.app.post_processing.nas_transfer_service import NASTransferService


def test_nas_transfer_service():
    # mocking the recording instance
    rec_id = '9_15'
    rec_instance = Recording(id=rec_id, activity_id=9, is_error=False, steps=[])
    data_dir = "../../../../data/"
    nas_transfer_service = NASTransferService(rec_instance, data_dir)
    nas_transfer_service.transfer_from_local_to_nas()


if __name__ == '__main__':
    test_nas_transfer_service()