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
parser.add_argument("-all", help="Download, cleanse and insert all available AIS data. NOTE: Will delete all entries in .log file and restart from first file.", required=False, default=False, action=argparse.BooleanOptionalAction)
parser.add_argument("--cont", help="Continue downloading, cleansing and inserting AIS-data from lastest downloaded file (read from .log-file)", required=False, default=False, action=argparse.BooleanOptionalAction)
parser.add_argument("--specific", help="Download, cleanse and insert a specific AIS-file and insert it. Name must be exact, without file-exstension",required=False, default="")
parser.add_argument("--interval", help="Download, cleanse and insert AIS-data in the interval given. Format: YYYY-MM-DD::YYY-MM-DD", required=False, default="")

args = parser.parse_args()

if args.all:
    dlais.begin(all=True)
elif args.cont:
    dlais.begin(cont=True)
elif args.specific:
    dlais.begin(file_to_download=args.specific)
elif args.interval:
    dlais.begin(interval_to_download=args.interval)


