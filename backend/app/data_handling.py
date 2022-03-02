from cmath import log
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests
import zipfile
import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import logging
import sys

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH')
ERROR_LOG_FILE_PATH = os.getenv('ERROR_LOG_FILE')
DIR_PATH = os.getenv('DIR_PATH')

# Logging for file
Log_Format = "[%(levelname)s] -  %(asctime)s - %(message)s"
logging.basicConfig(filename=ERROR_LOG_FILE_PATH,
                    filemode="w",
                    format = Log_Format,
                    encoding = 'utf-8',
                    level = logging.INFO)
logger = logging.getLogger()

# Logging for output in console
log_console = logging.StreamHandler(sys.stdout)
log_console.setLevel(logging.INFO)
log_console.setFormatter(Log_Format)

# Add console logger to our file logger
logger.addHandler(log_console)


# Establish connection to ais data
try:
    html = urlopen("https://web.ais.dk/aisdata/")
except HTTPError as e:
    logger.error(f"HTTP error: {e.code}. Site may be down, quitting program")
    quit()
except URLError as e:
    logger.error(f"Url-error: {e.reason}")
else:
    logger.info("Succesfully connected to website")


soup = BeautifulSoup(html, 'html.parser')

results = []
dates = []

for link in soup.find_all('a', href = True):
    if "aisdk" in link.string:
        results.append(link.string)
        dates.append(link.string.split("aisdk-")[1].split(".zip")[0])

def start():
    try:
        flog = open(LOG_FILE_PATH,'a+')
        flog.seek(0)
        data = flog.read().split('\n')
    except Exception as err:
        logger.error(f"Error when opening log file: {err} type: {type(err)}. Qutting program")
        quit()
    finally:
        flog.close()


    if len(data) <= 0:
        logger.error("Log file is empty, please insert the name of the latest downloaded ais file")
        quit()

    if data[-1] in '':
        current_latest_entry = data[-2]
    else:
        current_latest_entry = data[-1]

    logger.info(f"Latest entry is: {current_latest_entry}")

    latest_index = results.index(current_latest_entry)
    len_results = len(results)
    
    if latest_index + 1 == len_results:
        logger.info("No new entries available. Quitting.")
        quit()
    
    logger.info(f"There are {(len_results - 1) - latest_index} new entries available")

    for entry in range(latest_index + 1, len_results):
        logger.info(f"Trying to download file '{results[entry]}'")
        
        try:
            download_result = requests.get("https://web.ais.dk/aisdata/" + results[entry], allow_redirects=True)
            path_zip = DIR_PATH + results[entry]

            open(path_zip,'wb').write(download_result.content)
            logger.info("Download successfull, extracting file")

            with zipfile.ZipFile(path_zip, 'r') as zip_ref:
                zip_ref.extractall(DIR_PATH)

            logger.info("File has been extraced, deleting .zip file")
            os.remove(path_zip)
            logger.info(".zip file deleted")

        except Exception as err:
            logger.critical(f"Something went wrong when downloading/extracting the latest data: {err}, type: {type(err)}. Qutting program")
            quit()
        
        insert_into_db(DIR_PATH + results[entry].replace('.zip','.csv'), results[entry])


def insert_into_db(path_csv, name):
    logger.info("Connecting to database")
    try:
        conn = psycopg2.connect(database="aisdb", user=USER, password=PASS, host="db", port="5432")
        conn.autocommit = True
        cursor = conn.cursor()
    except Exception as err:
        logger.critical(f"Could not connect to the database: {err} error type: {type(err)}. Qutting program....")
        quit()

    sql = "COPY raw_data FROM STDIN WITH (format csv, delimiter E'\u002C', header true)"

    logger.info("Connection successful, opening CSV-file for copying")
    try:
        file = open(path_csv, 'r')
    except FileNotFoundError:
        logger.critical(f"CSV-file not found at path: {path_csv}. Qutting")
        quit()
    except Exception as err:
        logger.critical(f"Something went wrong when opening the csv file at: {path_csv}. Error: {err} Error type: {type(err)} Qutting")
        quit()

    logger.info(f"Inserting csv file '{name}' into raw_ais db...")
    try:
        cursor.copy_expert(sql, file)
        file.close()
        conn.commit()
        conn.close()
    except Exception as err:
        logger.critical(f"Something went wrong when inserting into the database: {err} error type: {type(err)}. Qutting")
        quit()

    logger.info("Insertion completed succesfully!")

    logger.info("Adding new file to log file")
    try:
        with open(LOG_FILE_PATH) as log_file:
            log_file.writelines(name)
            logger.info("Successfully added new file to log!")
    except IOError as e:
        logger.critical(f"IO error when accessing log file at {LOG_FILE_PATH}, error: {e}")
    else:
        logger.critical(f"Something went wrong when accessing log file at {LOG_FILE_PATH}, error: {e}, error type: {type(e)}")

start()