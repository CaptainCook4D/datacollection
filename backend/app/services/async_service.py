import logging
import asyncio
import os
import sys
import signal
import functools
import datetime

from .firebase_service import FirebaseService
from .recording_service import RecordingService
from ..utils.constants import Async_Constants as const
from ..models.recording import Recording
from ..utils.logger_config import get_logger

logger = get_logger(__name__)

# async def upload_task(recording_instance: Recording):
# 	# Create a DB service attached to the new child process
# 	db_service = FirebaseService()
# 	uploading_service = BoxService()
# 	uploading_service.upload_data(recording_instance, db_service)


def update_activity_recording_interrupt_handler(
		recording: Recording,
		db_service: FirebaseService,
		recording_service: RecordingService,
		signum,
		frame
):
	logger.info("Received interrupt signal {}".format(signum))
	
	recording_service.stop_recording()
	logger.info("Stopped all threads related to recording")
	
	updated_recording = db_service.fetch_recording(recording.id)

	updated_recording.recording_info.end_time = datetime.datetime.now().isoformat()
	db_service.update_recording(updated_recording)
	logger.info("Updated activity recording end time in Firebase Database")
	
	sys.exit(0)


async def activity_record_task(recording: Recording, db_service: FirebaseService):
	# Create a DB service attached to the new child process
	
	logger.info("Starting activity recording and updated start time in Firebase Database")
	recording.recording_info.start_time = datetime.datetime.now().isoformat()
	db_service.update_recording(recording)
	
	recording_service = RecordingService(recording)
	
	# Set the interrupt handler
	# Code that will be executed when signalled to stop
	signal.signal(
		signal.SIGINT,
		functools.partial(update_activity_recording_interrupt_handler, recording, db_service, recording_service)
	)
	
	# Starts necessary things for recording from hololens service
	logger.info("Starting data recording")
	recording_service.start_recording()


def create_async_subprocess(recording, async_type, db_service):
	pid = os.fork()
	if pid == 0:
		# This is the child process
		child_subprocess_pid = os.getpid()
		logger.info("Child process with PID - {}".format(child_subprocess_pid))
		
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		
		if async_type == const.ACTIVITY_RECORDING:
			loop.run_until_complete(activity_record_task(recording, db_service))
		
		return child_subprocess_pid
	else:
		# This is the parent process
		logger.info(f'Parent process with PID {pid}')
		# Return the PID of the child process
		return pid

# if __name__ == '__main__':
#     process_id = create_async_subprocess()
#     print("Started new asynchronous subprocess with PID", process_id)
#     # Exit the parent process
#     sys.exit(0)
