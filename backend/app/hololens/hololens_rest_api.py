import base64
import os.path
import time

import requests
from requests.auth import HTTPBasicAuth

# Reference for the Hololens2 Device portal API reference
# https://learn.microsoft.com/en-us/windows/mixed-reality/develop/advanced-concepts/device-portal-api-reference

HOLOLENS2_USERNAME = f"admin"
HOLOLENS2_PASSWORD = f"123456789"
ASCII = "ascii"

# Create an HTTPBasicAuth object that will be passed to requests
auth = HTTPBasicAuth(HOLOLENS2_USERNAME, HOLOLENS2_PASSWORD)


def base64_encode_string(string_value):
	string_bytes = string_value.encode(ASCII)
	base64_bytes = base64.b64encode(string_bytes)
	base64_string = base64_bytes.decode(ASCII)
	return base64_string


def base64_decode_string(base64_string):
	base64_bytes = base64_string.encode(ASCII)
	string_bytes = base64.b64decode(base64_bytes)
	string_value = string_bytes.decode(ASCII)
	return string_value


def send_rest_post_request(post_url, params=None):
	response = requests.post(post_url, auth=auth)
	if response.ok:
		print(response)
	pass


def send_rest_get_request(get_url, params=None):
	response = requests.get(get_url, auth=auth)
	return response


def get_hostname(ip_address):
	# Define the get URL to get the HostName
	get_url = f"http://{ip_address}/api/os/machinename"
	response = send_rest_get_request(get_url)
	if not response.ok:
		return None
	hostname = response.json()['ComputerName']
	return hostname


# MRC - Mixed Reality Capture
def start_mrc(ip_address):
	#  Need to check the MRC status - /api/holographic/mrc/status
	start_mrc_url = f"http://{ip_address}/api/holographic/mrc/video/control/start" \
					f"?holo=false&pv=true&mic=true&loopback=false&RenderFromCamera=true&vstab=true&vstabbuffer=30"
	send_rest_post_request(start_mrc_url)


def stop_mrc(ip_address):
	# Need to verify the stop mrc
	stop_mrc_url = f"http://{ip_address}/api/holographic/mrc/video/control/stop"
	send_rest_post_request(stop_mrc_url)
	pass


def get_mrc_files(ip_address):
	get_url = f"http://{ip_address}/api/holographic/mrc/files"
	response = send_rest_get_request(get_url)
	if not response.ok:
		return None
	json_response = response.json()
	return json_response


def download_most_recent_mrc_file(ip_address, download_location, prefix_file_name=None):
	json_response = get_mrc_files(ip_address)
	mrc_files_list = json_response['MrcRecordings']
	most_recent_mrc_file = mrc_files_list[-1]
	filename = most_recent_mrc_file['FileName']
	time_stamp = most_recent_mrc_file['CreationTime']
	if prefix_file_name is not None:
		video_filename = prefix_file_name + '_' + str(time_stamp) + '_' + filename
	else:
		video_filename = str(time_stamp) + "_" + filename
	video_path = os.path.join(download_location, video_filename)
	filename_hex64 = base64_encode_string(filename)
	stream = "stream"
	# "http://10.176.198.58/api/holographic/mrc/file?filename=MjAyMzAyMjBfMTYwMzUzX0hvbG9MZW5zLm1wNA==&op=stream"
	get_url = f"http://{ip_address}/api/holographic/mrc/file?filename={filename_hex64}&op={stream}"
	# NOTE the stream=True parameter below
	print("Downloading   : ", filename)
	with requests.get(get_url, stream=True, auth=auth) as r:
		r.raise_for_status()
		with open(video_path, 'wb') as f:
			for chunk in r.iter_content(chunk_size=8192):
				f.write(chunk)
	print("Downloaded to : ", video_path)
	return video_path


def main():
	ip_address = '10.176.198.58'
	hostname = get_hostname(ip_address)
	print(hostname)
	start_mrc(ip_address)
	print("Started Recording")
	time.sleep(10)
	stop_mrc(ip_address)
	print("Stopped Recording")
	get_mrc_files(ip_address)
	download_most_recent_mrc_file(ip_address, download_location="../../data")


if __name__ == '__main__':
	main()
