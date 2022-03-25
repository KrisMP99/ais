import os
import re
from dotenv import load_dotenv
import argparse
import logging
import download_ais_data as dlais

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH')
ERROR_LOG_FILE_PATH = os.getenv('ERROR_LOG_FILE_PATH')
DIR_PATH = os.getenv('DIR_PATH')

parser = argparse.ArgumentParser(description="AIS data downloading, cleansing and insertion")
parser.add_argument("-A", "-all", help="Download, cleanse and insert all available AIS data", required=False, default=False)
parser.add_argument("-C", "--cont", help="Continue downloading, cleansing and inserting AIS-data from last downloaded file (read from .log-file)", required=False, default=False)
parser.add_argument("-S", "--specific", help="Download, cleanse and insert a specific AIS-file and insert it. Name must be exact, without file-exstension",required=False, default="")
parser.add_argument("-I", "--interval", help="Download, cleanse and insert AIS-data in the interval given. Example: 01-01-2021::31-01-2021 -> will download, cleanse and insert all AIS data between 01-01-2021 and 31-01-2021 (interval dates included)", required=False, default="")

arguments = parser.parse_args()


def get_logger():
    Log_Format = "[%(levelname)s] -  %(asctime)s - %(message)s"
    logging.basicConfig(format = Log_Format,
                        force = True,
                        handlers = [
                            logging.FileHandler(ERROR_LOG_FILE_PATH),
                            logging.StreamHandler()
                        ],
                        level = logging.INFO)

    logger = logging.getLogger()
    return logger

if arguments.all:
    dlais.start(all=True)
elif arguments.cont:
    dlais.start(cont=True)
elif arguments.specific:
    dlais.start(file_to_download=arguments.specific)
elif arguments.interval:
    dlais.start(interval_to_download=arguments.interval)


