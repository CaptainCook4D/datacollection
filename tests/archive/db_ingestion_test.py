import os

from datacollection.user_app.backend.app.utils.db_ingest_utils import ActivitiesIngestion

if __name__ == "__main__":
	current_directory = os.getcwd()
	info_directory = os.path.join(current_directory, "../backend/info_files")
	
	# user_ingestion = UserIngestion(info_directory, remove_past_data=True)
	# user_ingestion.ingest()
	activities_ingestion = ActivitiesIngestion(info_directory, remove_past_data=True)
	activities_ingestion.ingest()
	# activity_recordings_ingestion = ActivityRecordingsIngestion(info_directory, remove_past_data=True)
	# activity_recordings_ingestion.ingest()