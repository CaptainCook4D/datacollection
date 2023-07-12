from datacollection.user_app.backend.app.utils.db_ingest_utils import ActivitiesIngestion, UserIngestion, EnvironmentIngestion, AnnotationAssignmentIngestion
import os

if __name__ == "__main__":
	current_directory = os.getcwd()
	info_directory = os.path.join(current_directory, "../backend/info_files")
	# info_directory = "info_files"
	
	# user_ingestion = UserIngestion(info_directory, remove_past_data=True)
	# user_ingestion.ingest()
	# activities_ingestion = ActivitiesIngestion(info_directory, remove_past_data=True)
	# activities_ingestion.ingest()
	
	# environment_ingestion = EnvironmentIngestion(info_directory, remove_past_data=True)
	# environment_ingestion.ingest()
	
	annotation_assignment_ingestion = AnnotationAssignmentIngestion(info_directory, remove_past_data=True)
	annotation_assignment_ingestion.ingest()
