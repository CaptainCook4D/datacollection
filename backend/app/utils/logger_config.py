import logging
import os
import datetime

from .constants import BASE_DIRECTORY

import logging.config


def setup_logging():
    # get the current date and time
    now = datetime.datetime.now()
    
    # format the date and time as a string
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    
    # Configure logging
    log_directory = os.path.join(BASE_DIRECTORY, 'logs')
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    
    log_file_path = os.path.join(log_directory, f"std.log")
    logging.basicConfig(filename=log_file_path, filemode='a', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')

    logging.getLogger('boxsdk').setLevel(logging.CRITICAL)


def get_logger(name):
    return logging.getLogger(name)

