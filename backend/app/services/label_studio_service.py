import json
import os
import random
import time

from .box_service import BoxService
from .firebase_service import FirebaseService
from ..models.annotation import Annotation
from ..models.recording import Recording
from ..utils.constants import Annotation_Constants as const
from ..utils.logger_config import get_logger

from label_studio_sdk import Client

logger = get_logger(__name__)


def create_directories(dir_path):
	if not os.path.exists(dir_path):
		os.makedirs(dir_path)


def generate_random_color():
	return '#' + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])


class LabelStudioService:
	
	def __init__(self):
		self.db_service = FirebaseService()
		self.box_service = BoxService()
		
		self.label_studio_client = Client(url=const.LABEL_STUDIO_URL, api_key=const.LABEL_STUDIO_API_AUTH_TOKEN)
		self.activity_xml_directory = "./info_files/project_xmls"
		create_directories(self.activity_xml_directory)
		self.annotations_backup_directory = "./info_files/annotations_backup"
		create_directories(self.annotations_backup_directory)
	
	def _save_activity_xml(self, activity_xml, recording):
		logger.info(f'Saving activity XML for recording {recording.id}')
		with open(f'{self.activity_xml_directory}/{recording.id}.xml', 'w') as file:
			file.write(activity_xml)
		logger.info(f'Activity XML saved for recording {recording.id}')
	
	def generate_project(self, recording: Recording):
		"""
		Generates a Label Studio project for a given recording ID.
		:param recording: The recording ID for which the project is to be generated.
		:return: The project ID of the generated project.
		"""
		# Fetch the recording details from the database.
		# recording = Recording.from_dict(self.db_service.fetch_recording(recording_id))
		recording_id = recording.id
		
		# Generate the recipe XML for the project.
		activity_xml = self.generate_activity_xml(recording)
		self._save_activity_xml(activity_xml, recording)
		
		# Project particulars
		project_name = f'{recording_id}_360p.mp4'
		video_path = f'{const.LOCAL_VIDEO_DIRECTORY_PATH}/{recording_id}_360p.mp4'
		label_config = activity_xml
		
		label_studio_projects = self.label_studio_client.get_projects()
		
		for label_studio_project in label_studio_projects:
			if label_studio_project.title == f'{project_name}':
				logger.info(f'{project_name} has been used previously for project ID {label_studio_project.id}.')
				return label_studio_project.id
		
		logger.info(f'{project_name} has not been used previously.')
		# Create a project with the specified name and XML file
		label_studio_project = self.label_studio_client.start_project(
			title=f'{project_name}',
			label_config=label_config
		)
		
		# Print the project ID
		logger.info(f'Project ID: {label_studio_project.id}')
		return label_studio_project.id
	
	def generate_activity_xml(self, recording: Recording):
		step_array = []
		for idx, step in enumerate(recording.steps):
			step_alias = ''
			if step.errors is not None and len(step.errors) > 0:
				for error in step.errors:
					step_alias += f' (ErrorTag:{error.tag}, ErrorDescription:{error.description}),'
				step_alias += f' (StepDescription: {step.description})'
			
			if step.modified_description is None or step.modified_description == '':
				description = step.description
				step_alias += f' (StepDescription: {step.description})'
			else:
				description = step.modified_description
				step_alias += f', (StepModifiedDescription: {step.modified_description})'

			step_array.append({'step_number': idx, 'modified_description': description, 'step_alias': step_alias})
		
		xml_string = '<View>\n'
		xml_string += f'  <Header value="Labeling Recording ID {recording.id}"/>\n'
		xml_string += '  <Video name="video" value="$video_url" sync="audio"/>\n'
		xml_string += '  <View style="display:flex;align-items:start;gap:8px;flex-direction:column">\n'
		xml_string += '    <AudioPlus name="audio" value="$video_url" sync="video" speed="true"/>\n'
		xml_string += '    <View>\n'
		xml_string += '      <Filter toName="action" minlength="0" name="filter"/>\n'
		xml_string += '      <Labels name="action" toName="audio" choice="single" showInline="true">\n'
		xml_string += '        <Label value="Type Action." background="#000000"/>\n'
		for activity_step in step_array:
			random_color = generate_random_color()
			xml_string += f"<Label alias=\"{activity_step['step_alias']}\" value=\"S{activity_step['step_number']}: {activity_step['modified_description']}\"  background=\"{random_color}\"/>\n"
		xml_string += '      </Labels>\n'
		xml_string += '    </View>\n'
		xml_string += '  </View>\n'
		xml_string += '  <View visibleWhen="region-selected" whenLabelValue="Type Action.">\n'
		xml_string += '    <Header value="Provide Transcription"/>\n'
		xml_string += '    <TextArea name="transcription" toName="audio" rows="2" editable="true" perRegion="true" required="false"/>\n'
		xml_string += '  </View>\n'
		xml_string += '</View>'
		return xml_string
	
	def fetch_project_id_to_annotation_map(self):
		annotations = dict(self.db_service.fetch_annotations())
		annotations = [Annotation.from_dict(annotation) for annotation in annotations.values()]
		
		project_id_to_annotation_map = {}
		for annotation in annotations:
			project_id_to_annotation_map[annotation.label_studio_project_id] = annotation
		
		return project_id_to_annotation_map
	
	def backup_all_annotations_projects(self):
		label_studio_projects = self.label_studio_client.get_projects()
		project_id_to_annotation_map = self.fetch_project_id_to_annotation_map()
		
		for label_studio_project in label_studio_projects:
			self.backup_annotations_project(project_id_to_annotation_map[label_studio_project.id])
	
	def backup_annotations_project(self, annotation: Annotation):
		# Generate a human-readable timestamp for the backup file name
		# Move the backup directory to its final location with the timestamped name
		label_studio_project = self.label_studio_client.get_project(annotation.label_studio_project_id)
		
		annotations = label_studio_project.export_tasks()
		
		if len(annotations) == 0:
			logger.info(f"No annotations found for project '{label_studio_project.title}'")
			return
		
		current_timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
		
		project_name = label_studio_project.title.replace('mp4', 'json')
		
		backup_annotation_directory_path = f"{self.annotations_backup_directory}/{current_timestamp}"
		create_directories(backup_annotation_directory_path)
		backup_annotation_file_path = f"{self.annotations_backup_directory}/{current_timestamp}/{project_name}"
		
		with open(backup_annotation_file_path, 'w') as backup_file:
			json.dump(annotations, backup_file)
		logger.info(f"Backup created for project '{project_name}' at '{backup_annotation_file_path}'")
		
		# Update annotation in Database
		annotation.annotation_json = annotations
		self.db_service.update_annotation(annotation)
		
		# Upload updated annotations to BOX
		self.box_service.upload_annotation(annotation, backup_annotation_file_path)
	
	def delete_all_label_studio_projects(self):
		"""
		Deletes all projects from Label Studio.
		"""
		projects = self.label_studio_client.get_projects()
		logger.info(f'Deleting all projects from Label Studio')
		for project in projects:
			self.label_studio_client.delete_project(project.id)
		logger.info(f'All projects deleted from Label Studio')
	
	def delete_label_studio_project(self, label_studio_project_id):
		projects = self.label_studio_client.get_projects()
		logger.info(f'Deleting project {label_studio_project_id} from Label Studio')
		for project in projects:
			if project.id == label_studio_project_id:
				self.label_studio_client.delete_project(project.id)
				break
		logger.info(f'Project {label_studio_project_id} deleted from Label Studio')
	
	def delete_annotation_project(self, annotation: Annotation):
		self.label_studio_client.delete_project(annotation.label_studio_project_id)
		self.db_service.delete_annotation(annotation.annotation_id)
	
	def delete_all_annotations_projects(self):
		project_id_to_annotation_map = self.fetch_project_id_to_annotation_map()
		projects = self.label_studio_client.get_projects()
		logger.info(f'Deleting all projects from Label Studio')
		for project in projects:
			self.delete_annotation_project(project_id_to_annotation_map[project.id])
			
	def delete_all_activity_annotations_projects(self, activity_id, user_id):
		project_id_to_annotation_map = self.fetch_project_id_to_annotation_map()
		projects = self.label_studio_client.get_projects()
		logger.info(f'Deleting all projects from Label Studio')
		for project in projects:
			annotation = project_id_to_annotation_map[project.id]
			annotation_activity_id = annotation.recording_id.split('_')[0]
			if str(annotation_activity_id) == str(activity_id) and str(annotation.user_id) == str(user_id):
				self.delete_annotation_project(project_id_to_annotation_map[project.id])
