import os
from dotenv import load_dotenv
import argparse
import logging

from parso import parse
from handle_ais_data import start 

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH')
ERROR_LOG_FILE_PATH = os.getenv('ERROR_LOG_FILE_PATH')
DIR_PATH = os.getenv('DIR_PATH')

# Logging for file
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

def parse_args():
    parser = argparse.ArgumentParser(description="AIS data downloading, cleansing and insertion")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a","-all", metavar='', help="Download, cleanse and insert all available AIS data. NOTE: Will delete all entries in .log file and restart from first file.", dest="all", required=False, default=False, type=bool)
    group.add_argument("-c","--cont", metavar='', help="Continue downloading, cleansing and inserting AIS-data from lastest downloaded file (read from .log-file)", dest="cont", required=False, default=False, type=bool)
    group.add_argument("-s","--specific",metavar='', help="Download, cleanse and insert a specific AIS-file and insert it. Example: 'aisdk-2022-01-01.zip'", dest="specific", required=False, default=None, type=str)
    group.add_argument("-i","--interval", metavar='', help="Download, cleanse and insert AIS-data in the interval given. Format: YYYY-MM-DD::YYY-MM-DD", dest="interval", required=False, default=None, type=str)
    group.add_argument("-f", "--from_folder", metavar='', help="Will only process and insert the data of the .csv files located in the 'CSV_FILES_PATH' .env variable", dest="from_folder", required=False, default=False, type=bool)
    args = parser.parse_args()
    return args

def main():
    logger = get_logger()
    args = parse_args()
    if args.all:
        start(all=True, logger=logger)
    elif args.cont:
        start(cont=True, logger=logger)
    elif args.specific:
        start(file_to_download=args.specific, logger=logger)
    elif args.interval:
        start(interval_to_download=args.interval, logger=logger)
    elif args.from_folder:
        start(only_from_folder=True, logger=logger)


if __name__ == "__main__":
    main()
    


