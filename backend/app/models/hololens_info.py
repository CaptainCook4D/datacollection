import json

from ..utils.constants import Recording_Constants as const


class HololensInfo:
	
	def __init__(self):
		self.pv = True
		self.mc = True
		self.depth_ahat = True
		self.spatial = True

		self.imu = True
		self.imu_accelerometer = True
		self.imu_gyroscope = True
		self.imu_magnetometer = True
		
		self.depth_lt = False
		self.vlc_leftleft = False
		self.vlc_leftfront = False
		self.vlc_rightright = False
		self.vlc_rightfront = False
		
		self.device_ip = const.DEFAULT_HOLOLENS_IP
		
	def is_disabled(self):
		return not self.pv and not self.mc and not self.depth_ahat and not self.spatial and not self.depth_lt \
		       and not self.vlc_leftleft and not self.vlc_leftfront and not self.vlc_rightright \
		       and not self.vlc_rightfront and not self.imu_accelerometer and not self.imu_gyroscope \
		       and not self.imu_magnetometer and not self.imu
	
	def is_enabled(self):
		return not self.is_disabled()
	
	def to_dict(self):
		return {
			const.PHOTOVIDEO: self.pv,
			const.MICROPHONE: self.mc,
			const.DEPTH_AHAT: self.depth_ahat,
			const.SPATIAL: self.spatial,
			const.DEPTH_LT: self.depth_lt,
			const.VLC_LEFTLEFT: self.vlc_leftleft,
			const.VLC_LEFTFRONT: self.vlc_leftfront,
			const.VLC_RIGHTRIGHT: self.vlc_rightright,
			const.VLC_RIGHTFRONT: self.vlc_rightfront,
			const.DEVICE_IP: self.device_ip,
			const.IMU: self.imu,
			const.IMU_ACCELEROMETER: self.imu_accelerometer,
			const.IMU_GYROSCOPE: self.imu_gyroscope,
			const.IMU_MAGNETOMETER: self.imu_magnetometer
		}
	
	@classmethod
	def from_dict(cls, hololens_info_dict):
		hololens_info = cls()
		
		hololens_info.pv = hololens_info_dict[const.PHOTOVIDEO]
		hololens_info.mc = hololens_info_dict[const.MICROPHONE]
		hololens_info.depth_ahat = hololens_info_dict[const.DEPTH_AHAT]
		hololens_info.spatial = hololens_info_dict[const.SPATIAL]
		hololens_info.depth_lt = hololens_info_dict[const.DEPTH_LT]
		hololens_info.vlc_leftleft = hololens_info_dict[const.VLC_LEFTLEFT]
		hololens_info.vlc_leftfront = hololens_info_dict[const.VLC_LEFTFRONT]
		hololens_info.vlc_rightright = hololens_info_dict[const.VLC_RIGHTRIGHT]
		hololens_info.vlc_rightfront = hololens_info_dict[const.VLC_RIGHTFRONT]

		# ToDo: Separate IMU is not yet implemented in frontend and need to change after the update
		if const.IMU in hololens_info_dict:
			hololens_info.imu = hololens_info_dict[const.IMU]
			hololens_info.imu_accelerometer = hololens_info_dict[const.IMU]
			hololens_info.imu_gyroscope = hololens_info_dict[const.IMU]
			hololens_info.imu_magnetometer = hololens_info_dict[const.IMU]

		hololens_info.device_ip = const.DEFAULT_HOLOLENS_IP
		# if const.DEVICE_IP in hololens_info_dict and hololens_info_dict[const.DEVICE_IP] != "":
		# 	hololens_info.device_ip = hololens_info_dict[const.DEVICE_IP]
		# else:
		# 	hololens_info.device_ip = const.DEFAULT_HOLOLENS_IP
		
		return hololens_info
	
	def __str__(self):
		return json.dumps(self.to_dict())
