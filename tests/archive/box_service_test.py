from datacollection.user_app.backend.models.recording import Recording
from datacollection.user_app.backend.services.box_service import BoxService

if __name__ == '__main__':
    box_service = BoxService()
    rec_id = '13_43'
    rec_instance = Recording(id=rec_id, activity_id=13, is_error=False, steps=[])
    recording_data_file_path = f'/home/ptg/CODE/data/gopro/{rec_id}_360p.mp4'
    box_service.upload_go_pro_360_video(rec_instance, recording_data_file_path)