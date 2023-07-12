from ..utils.constants import Annotation_Constants as const


class AnnotationAssignment:
	
	def __init__(self, user_id, username, activities):
		self.user_id = user_id
		self.username = username
		self.activities = activities
	
	def __str__(self):
		return f'AnnotationAssignment(user_id={self.user_id}, username={self.username}, activities={self.activities})'
	
	def to_dict(self):
		return {
			const.USER_ID: self.user_id,
			const.USERNAME: self.username,
			const.ACTIVITIES: self.activities
		}
	
	@staticmethod
	def from_dict(annotation_assignment_dict):
		return AnnotationAssignment(
			user_id=annotation_assignment_dict[const.USER_ID],
			username=annotation_assignment_dict[const.USERNAME],
			activities=annotation_assignment_dict[const.ACTIVITIES]
		)
