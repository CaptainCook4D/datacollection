from ..utils.constants import User_Constants as const


class UserEnvironment:
	
	def __init__(self, id, username, environment_name=None):
		self._id = id
		self._username = username
		self._environment_name = environment_name
	
	def __str__(self):
		return f"User(id={self._id}, username={self._username}), environment_name={self._environment_name})"
	
	def to_dict(self):
		return {
			const.ID: self._id,
			const.USERNAME: self._username,
			const.ENVIRONMENT_NAME: self._environment_name
		}
	
	def get_id(self):
		return self._id
	
	def get_username(self):
		return self._username
	
	def get_environment_name(self):
		return self._environment_name
	
	def set_id(self, id):
		self._id = id
		
	def set_username(self, username):
		self._username = username
		
	def set_environment_name(self, environment_name):
		self._environment_name = environment_name
		
	def set_user(self, user):
		self._id = user.get_id()
		self._username = user.get_username()
		self._environment_name = user.get_environment_name()
	
	@staticmethod
	def from_dict(user_dict):
		return UserEnvironment(
			id=user_dict[const.ID],
			username=user_dict[const.USERNAME],
			environment_name=user_dict[const.ENVIRONMENT_NAME]
		)
	
	
	