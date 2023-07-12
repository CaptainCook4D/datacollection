from datacollection.user_app.backend.app.models.activity import Activity
from datacollection.user_app.backend.app.models.environment import Environment
from datacollection.user_app.backend.app.models.recording import Recording
from datacollection.user_app.backend.app.models.user import User
from datacollection.user_app.backend.app.services.firebase_service import FirebaseService

if __name__ == "__main__":
	db_service = FirebaseService()
	
	# 1. Fetch all activities
	activities_list = db_service.fetch_activities()
	activities = [Activity.from_dict(activity) for activity in activities_list if activity is not None]
	activity_id_name_map = {activity.id: activity.name for activity in activities}
	
	# 2. Fetch all recordings
	recordings = []
	user_recordings = dict(db_service.fetch_all_selected_recordings())
	for recording_id, user_recording_dict in user_recordings.items():
		recording = Recording.from_dict(user_recording_dict)
		recordings.append(recording)
	
	# 3. Fetch all environments
	environments_list = db_service.fetch_environments()
	environments = [Environment.from_dict(environment) for environment in environments_list if
	                environment is not None]
	environment_id_name_map = {environment.get_id(): environment.get_name() for environment in environments}
	
	# 4. Fetch all users
	users_list = db_service.fetch_users()
	users = [User.from_dict(user) for user in users_list if user is not None]
	user_id_name_map = {user.id: user.username for user in users}
	
	with open("activity_recordings.txt", "a") as activity_file:
		for activity in activities:
			activity_file.write(f"------------------------------------\n")
			activity_file.write(f"Activity ID:{activity.id} - {activity.name}\n")
			activity_file.write(f"------------------------------------\n")
			for recording in recordings:
				if recording.activity_id == activity.id:
					activity_file.write(f"Recording ID: {recording.id}, selected by {recording.selected_by}:{user_id_name_map[recording.selected_by]} recorded by {recording.recorded_by} at {environment_id_name_map[recording.environment]}\n")
			activity_file.write(f"\n\n")
