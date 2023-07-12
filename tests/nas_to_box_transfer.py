from datacollection.user_app.backend.app.models.recording import Recording
from datacollection.user_app.backend.app.post_processing.nas_to_box_post_processing_service import \
	NasToBoxPostProcessingService
from datacollection.user_app.backend.app.services.firebase_service import FirebaseService

if __name__ == '__main__':
	db_service = FirebaseService()
	recording_id_list = ["2_22", "16_40", "21_28", "22_31", "22_10", "26_24", "26_136"]
	for recording_id in recording_id_list:
		recording_dict = db_service.fetch_recording(recording_id)
		recording = Recording.from_dict(recording_dict)
		nas_to_box_service = NasToBoxPostProcessingService(recording)
