from datacollection.user_app.backend.app.models.recording import Recording
from datacollection.user_app.backend.app.post_processing.recording_post_processing_service import RecordingPostProcessingService


def test_sync_pv_base():
    data_parent_dir = "../../../../../data"
    rec_ids = [
        "13_43",
    ]
    for rec_id in rec_ids:
        rec_instance = Recording(id=rec_id, activity_id=0, is_error=False, steps=[])


if __name__ == '__main__':
    post_processing_service = RecordingPostProcessingService()