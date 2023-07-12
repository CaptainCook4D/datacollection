from .user_environment import UserEnvironment
from ..utils.constants import Environment_Constants as const


class Environment:
	
	def __init__(self, id, users_environments, name):
		self._id = id
		self._name = name
		self._users_environments = users_environments
	
	def get_id(self):
		return self._id
	
	def get_name(self):
		return self._name
	
	def get_users_environments(self):
		return self._users_environments
	
	def __str__(self):
		return f"Environment: ID: {self._id} - USERS: {self._users_environments}"
	
	def to_dict(self):
		users_environments = []
		for user_environment in self._users_environments:
			users_environments.append(user_environment.to_dict())
		
		return {
			const.ID: self._id,
			const.USERS: users_environments,
			const.NAME: self._name
		}
	
	@staticmethod
	def from_dict(environment_dict):
		return Environment(id=environment_dict[const.ID],
		                   users_environments=[UserEnvironment.from_dict(user_environment_dict) for
		                                       user_environment_dict in environment_dict[const.USERS]],
		                   name=environment_dict[const.NAME])
	
	def set_id(self, id):
		self._id = id
	
	def set_users_environments(self, users_environments):
		self._users_environments = users_environments
	
	def add_user_environment(self, user_environment):
		self._users_environments.append(user_environment)
	
	def remove_user_environment(self, user_environment):
		self._users_environments.remove(user_environment)
	
	def remove_all_users_environments(self):
		self._users_environments.clear()
	
	def get_user_environment(self, user_id) -> UserEnvironment:
		for user_environment in self._users_environments:
			if user_environment.get_id() == user_id:
				return user_environment
		return None
	
	def get_user_environments(self, user_id):
		user_environments = []
		for user_environment in self._users_environments:
			if user_environment.get_user_id() == user_id:
				user_environments.append(user_environment)
		return user_environments
	
	def get_user_environment_by_environment_name(self, environment_name):
		for user_environment in self._users_environments:
			if user_environment.get_environment_name() == environment_name:
				return user_environment
		return None
