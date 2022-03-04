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

# Establish connection to ais data
def connect_to_to_ais_web_server_and_get_data(logger):
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
    return results

def start():
    logger = get_logger()
    results = connect_to_to_ais_web_server_and_get_data(logger)

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
        
        insert_into_db(DIR_PATH + results[entry].replace('.zip','.csv'), results[entry], logger)


def insert_into_db(path_csv, name, logger):
    logger.info("Connecting to database")
    try:
        conn = psycopg2.connect(database="aisdb", user=USER, password=PASS, host="db", port="5432")
        conn.autocommit = True
        cursor = conn.cursor()
    except Exception as err:
        logger.critical(f"Could not connect to the database: {err} error type: {type(err)}. Qutting program....")
        quit()

    sql = "COPY raw_data(timestamp, mobile_type, mmsi, latitude, longitude, navigational_status, rot, sog, cog, heading, imo, callsign, name, ship_type, cargo_Type, width, length, type_of_position_fixing_device, draught, destination, eta, data_source_type, a, b, c, d) FROM STDIN WITH (format csv, delimiter E'\u002C', header true)"

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
        with open(LOG_FILE_PATH, 'a+') as log_file:
            log_file.seek(0)
            data = log_file.read(100)
            if len(data) > 0:
                log_file.write("\n")
            log_file.write(name)
            logger.info("Successfully added new file to log!")
    except IOError as e:
        logger.critical(f"IO error when accessing log file at {LOG_FILE_PATH}, error: {e}")
    except Exception as e:
        logger.critical(f"Something went wrong when accessing log file at {LOG_FILE_PATH}, error: {e}, error type: {type(e)}")

def insert_csv_to_db_manually(path_csv):
    logger = get_logger()
    logger.info("Connecting to database...")
    try:
        conn = psycopg2.connect(database="aisdb", user=USER, password=PASS, host="db", port="5432")
        conn.autocommit = True
        cursor = conn.cursor()
    except Exception as err:
        logger.critical(f"Could not connect to the database: {err} error type: {type(err)}. Qutting program....")
        quit()

    logger.info("Connection successful, opening CSV-file for copying")
    try:
        file = open(path_csv, 'r')
    except FileNotFoundError:
        logger.critical(f"CSV-file not found at path: {path_csv}. Qutting")
        quit()
    except Exception as err:
        logger.critical(f"Something went wrong when opening the csv file at: {path_csv}. Error: {err} Error type: {type(err)} Qutting")
        quit()

    logger.info("Creating temp table...")
    try:
        cursor.execute("CREATE TEMPORARY TABLE raw_temp (LIKE raw_data)")
        cursor.execute("ALTER TABLE raw_temp ALTER COLUMN mmsi TYPE VARCHAR, ALTER COLUMN imo TYPE VARCHAR")
    except Exception as err:
        logger.critical(f"Could not create/alter temp. table: {err}")
        quit()

    sql = "COPY raw_temp FROM STDIN WITH (format csv, delimiter E'\u002C', header true)"

    logger.info("Copying data into temp_table")
    try:
        cursor.execute("SET datestyle = DMY")
        cursor.copy_expert(sql, file)
        file.close()
    except Exception as err:
        logger.critical(f"Could not copy data to temp. table: {err}")
        quit()

    logger.info("Removing 'Unknown' from mmsi and imo and inserting into raw_data")
    try:
        cursor.execute("UPDATE raw_temp SET mmsi = (CASE WHEN mmsi = 'Unknown' THEN 'NULL' END), imo = (CASE WHEN imo = 'Unknown' THEN 'NULL' END) WHERE mmsi IN ('Unknown') OR imo in ('Unknown')")
        cursor.execute("INSERT INTO raw_data SELECT * FROM raw_temp")
    except Exception as err:
        logger.critical(f"Could not update/insert into raw_data {err}")
        quit()

    conn.commit()
    conn.close()

    logger.info("Done!")

insert_csv_to_db_manually("/srv/data/csv/aisdk-2022-01-01.csv")

#start()

# (timestamp, mobile_type, mmsi, latitude, longitude, navigational_status, rot, sog, cog, heading, imo, callsign, name, ship_type, cargo_Type, width, length, type_of_position_fixing_device, draught, destination, eta, data_source_type, a, b, c, d)