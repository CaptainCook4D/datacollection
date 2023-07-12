from ..utils.constants import Annotation_Constants as const


class Annotation:
	
	def __init__(self, recording_id, user_id, label_studio_project_id):
		self.recording_id = recording_id
		self.user_id = user_id
		self.label_studio_project_id = label_studio_project_id
		
		self.annotation_id = self.recording_id + '_' + str(self.user_id)
		self.annotation_json = None
	
	def to_dict(self):
		return {
			const.ANNOTATION_ID: self.annotation_id,
			const.RECORDING_ID: self.recording_id,
			const.USER_ID: self.user_id,
			const.LABEL_STUDIO_PROJECT_ID: self.label_studio_project_id,
			const.ANNOTATION_JSON: self.annotation_json
		}
	
	def response_to_dict(self):
		return {
			const.ANNOTATION_ID: self.annotation_id,
			const.RECORDING_ID: self.recording_id,
			const.USER_ID: self.user_id,
			const.LABEL_STUDIO_PROJECT_ID: self.label_studio_project_id
		}
	
	@staticmethod
	def from_dict(annotation_dict):
		annotation = Annotation(annotation_dict[const.RECORDING_ID], annotation_dict[const.USER_ID], annotation_dict[const.LABEL_STUDIO_PROJECT_ID])
		assert annotation.annotation_id == annotation_dict[const.ANNOTATION_ID]
		if const.ANNOTATION_JSON in annotation_dict:
			annotation.annotation_json = annotation_dict[const.ANNOTATION_JSON]
		return annotation
