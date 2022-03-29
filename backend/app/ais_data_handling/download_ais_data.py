import re
from time import time
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests
import zipfile
import os
import psycopg2
from dotenv import load_dotenv
import logging
import glob
import rarfile
import trips_partitioning as trp
import data_insertion as di
import douglas_peucker as dpe

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH')
ERROR_LOG_FILE_PATH = os.getenv('ERROR_LOG_FILE_PATH')
DIR_PATH = os.getenv('DIR_PATH')

raw_data_table_query = "CREATE TABLE IF NOT EXISTS raw_data ( \
                        timestamp TIMESTAMP WITHOUT TIME ZONE,\
                        type_of_mobile VARCHAR,\
                        mmsi integer,\
                        latitude real,\
                        longitude real,\
                        navigational_status VARCHAR,\
                        rot numeric,\
                        sog numeric,\
                        cog numeric,\
                        heading smallint,\
                        imo integer,\
                        callsign VARCHAR,\
                        name VARCHAR,\
                        ship_type VARCHAR,\
                        cargo_type VARCHAR,\
                        width smallint,\
                        length smallint,\
                        type_of_position_fixing_device VARCHAR,\
                        draught numeric,\
                        destination VARCHAR,\
                        eta TIMESTAMP WITHOUT TIME ZONE,\
                        data_source_type VARCHAR,\
                        a smallint,\
                        b smallint,\
                        c smallint, \
                        d smallint)" 

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

def get_latest_from_log(logger):
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

    return current_latest_entry.replace('csv','.zip') 


def get_start_end_indexes(begin_index_str, end_index_str, results, logger):
    begin_index_str = begin_index_str.replace('.csv','.zip')

    if end_index_str is not None:
        end_index_str = end_index_str.replace('.csv','.zip')

    if begin_index_str in results:
        start_index = results.index(begin_index_str)
    elif begin_index_str.replace('.zip','.rar') in results:
        begin_index_str = begin_index_str.replace('.zip','.rar')
        start_index = results.index(begin_index_str)
    else:
        logger.critical(f"Could not find file {begin_index_str} on site.")
        quit()
    
    if end_index_str is not None:
        if end_index_str in results:
            end_index = results.index(end_index_str)
        elif end_index_str.replace('.zip','.rar') in results:
            end_index = results.index(end_index_str.replace('.zip','.rar'))
    else:
        end_index = results.index(begin_index_str)
    
    return start_index, end_index

def start(files_to_download=None, cont = False, all = False):
    logger = get_logger()
    results = connect_to_to_ais_web_server_and_get_data(logger)

    if cont:
        begin_index_str = get_latest_from_log(logger)
        if not begin_index_str:
            logger.critical("No file to continue from. Please add a file to continue from in the log file.")
            quit()
        end_index_str = results[-1]
        logger.info(f"Latest entry is: {begin_index_str}")
    elif all:
        # change this
        begin_index_str = 'aisdk-2006-03.zip'
        end_index_str = results[-1]
    elif len(files_to_download) > 1:
        begin_index_str = files_to_download[0]
        end_index_str = None
    elif len(files_to_download) == 1:
        begin_index_str = files_to_download[0]
        end_index_str = None
    else:
        logger.critical("Something went wrong when determining which file(s) to download... Qutting!")
        quit()

    start_index, end_index = get_start_end_indexes(begin_index_str, end_index_str, results, logger)

    len_results = len(results)
 
    if(cont):
        if start_index + 1 == len_results:
            logger.info("No new entries available. Quitting.")
            quit()
        start_index += 1
        logger.info(f"There are {(len_results - 1) - start_index} new entries available")

    # We download the files and insert them into the database
    download_files_and_insert(start_index, end_index, results, logger)
    

def download_files_and_insert(start_index, end_index, results, logger):
    # Numpy for ?
    for entry in range(start_index, end_index):
        logger.info(f"Trying to download file '{results[entry]}'")
        try:
            download_result = requests.get("https://web.ais.dk/aisdata/" + results[entry], allow_redirects=True)
            download_result.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.warning(f"Received HTTP error {http_err} when trying to download file {results[entry]}. Skipping this file.")
            continue
        except requests.exceptions.ConnectionError as conn_err:
            logger.critical(f"Could not connect to web-server to download file {results[entry]}. Received connection error: {conn_err}. Qutting..")
            quit()
        except requests.exceptions.Timeout as time_err:
            logger.warning(f"We timed out when trying to download file {results[entry]}. Error: {time_err}. Skipping this file.")
            continue
        except requests.exceptions.RequestException as re_error:
            logger.warning(f"Something went wrong when requesting to download file {results[entry]}. Error: {re_error}. Skipping this file.")
            continue

        path_zip = DIR_PATH + results[entry]
        
        try:
            f = open(path_zip,'wb')
            f.write(download_result.content)
            logger.info("Download successful, extracting file.")
        except Exception as e:
            logger.warning(f"Could not save file {path_zip}. Error: {e}. Skipping this file.")
            continue
        finally:
            f.close()
        
        try:
            if ".zip" in path_zip: 
                with zipfile.ZipFile(path_zip, 'r') as zip_ref:
                    zip_ref.extractall(DIR_PATH)
            elif ".rar" in path_zip:
                with rarfile.RarFile(path_zip) as rar_ref:
                    rar_ref.extractall(path=DIR_PATH)
            else:
                logger.warning("Could not extract file at {path_zip}. Unsupported file format (not .zip or .rar). Skipping this file!")
                continue
                
            logger.info("File has been extraced, deleting compressed file")
            os.remove(path_zip)
            logger.info("Compressed file deleted")

        except Exception as err:
            logger.critical(f"Something went wrong when extracting the file: {err}, type: {type(err)}. Skipping this file.")
            continue
        
        if ".zip" in results[entry]:
            name = results[entry].replace('.zip','.csv')
        else:
            name = results[entry].replace('.rar','.csv')

        insert_into_db(DIR_PATH + name, results[entry], logger)


def insert_into_db(path_csv, name, logger):
    logger.info("Connecting to database")
    try:
        conn = psycopg2.connect(database="aisdb", user=USER, password=PASS, host="localhost", port="5432")
        conn.autocommit = True
        cursor = conn.cursor()
    except psycopg2.OperationalError as op_err:
        logger.critical(f"Something went wrong when connecting to the database: {op_err}")
        quit()


    logger.info("Connection successful, opening CSV-file for copying")
    try:
        file = open(path_csv, 'r')
    except FileNotFoundError:
        logger.warning(f"CSV-file not found at path: {path_csv}. Trying next file.")
        return
    except Exception as err:
        logger.warning(f"Something went wrong when opening the csv file at: {path_csv}. Error: {err} Error type: {type(err)}. Trying next file.")
        return

    logger.info("Creating raw_data and temp_table.")
    try:
        cursor.execute(raw_data_table_query)
        cursor.execute("CREATE TEMPORARY TABLE raw_temp (LIKE raw_data)")
        cursor.execute("ALTER TABLE raw_temp ALTER COLUMN mmsi TYPE VARCHAR, ALTER COLUMN imo TYPE VARCHAR")
    except Exception as err:
        logger.critical(f"Could not create/alter raw_data/temp. table: {err}. Trying next file!")
        conn.rollback()
        return
    
    sql = "COPY raw_temp FROM STDIN WITH (format csv, delimiter E'\u002C', header true)"
    logger.info("Copying data into temp_table")
    try:
        cursor.execute("SET datestyle = DMY")
        cursor.copy_expert(sql, file)
        file.close()
    except Exception as err:
        logger.critical(f"Could not copy data to temp. Error: {err}. Trying next file.")
        conn.rollback()
        return
    
    logger.info("Removing 'Unknown' from mmsi and imo and inserting into raw_data")
    try:
        cursor.execute("UPDATE raw_temp SET mmsi = (CASE WHEN mmsi = 'Unknown' THEN NULL END), imo = (CASE WHEN imo = 'Unknown' THEN NULL END) WHERE mmsi IN ('Unknown') OR imo in ('Unknown')")
        cursor.execute("ALTER TABLE raw_temp ALTER COLUMN mmsi TYPE INTEGER USING (mmsi::integer), ALTER COLUMN imo TYPE INTEGER USING (imo::integer)")
        cursor.execute("INSERT INTO raw_data SELECT  * FROM raw_temp")
    except Exception as err:
        logger.critical(f"Could not update/insert into raw_data {err}. Trying for next file!")
        conn.rollback()
        return

    conn.commit()
    conn.close()

    logger.info("Insertion to raw_data completed succesfully!")
    logger.info("Started data cleansing and trip partitioning.")
    cleanse_data_and_insert(logger)
    add_new_file_to_log(name, logger)
    
def cleanse_data_and_insert(logger):
    trip_list = trp.get_cleansed_data(logger)
    di.insert_cleansed_data(trip_list)
    quit()
    trip_list = dpe.create_line_strings(trip_list, logger)
    di.insert_into_star(logger)
    return

def add_new_file_to_log(file_name, logger):
    logger.info("Adding new file to log file")
    try:
        with open(LOG_FILE_PATH, 'a+') as log_file:
            log_file.seek(0)
            data = log_file.read(100)
            if len(data) > 0:
                log_file.write("\n")
            log_file.write(file_name.replace('.zip', '.csv'))
            logger.info("Successfully added new file to log!")
    except IOError as e:
        logger.critical(f"IO error when accessing log file at {LOG_FILE_PATH}, error: {e}")
    except Exception as e:
        logger.critical(f"Something went wrong when accessing log file at {LOG_FILE_PATH}, error: {e}, error type: {type(e)}")

def insert_csv_to_db_manually(path_csv):
    logger = get_logger()
    logger.info("Connecting to database...")
    try:
        conn = psycopg2.connect(database="aisdb", user=USER, password=PASS, host="localhost", port="5432")
        conn.autocommit = True
        cursor = conn.cursor()
    except Exception as err:
        logger.critical(f"Could not connect to the database: {err} error type: {type(err)}. Qutting program....")
        quit()

    logger.info(f"Connection successful, opening {path_csv.split('/')[-1]} for copying")
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
        cursor.execute("UPDATE raw_temp SET mmsi = (CASE WHEN mmsi = 'Unknown' THEN NULL END), imo = (CASE WHEN imo = 'Unknown' THEN NULL END) WHERE mmsi IN ('Unknown') OR imo in ('Unknown')")
        cursor.execute("ALTER TABLE raw_temp ALTER COLUMN mmsi TYPE INTEGER USING (mmsi::integer), ALTER COLUMN imo TYPE INTEGER USING (imo::integer)")
        cursor.execute("INSERT INTO raw_data SELECT  * FROM raw_temp")
    except Exception as err:
        logger.critical(f"Could not update/insert into raw_data {err}")
        quit()

    conn.commit()
    conn.close()

    logger.info("Done!")

# Grabs all the .csv files from a folder and inserts them into the database
def insert_csv_from_folder(folder_path):
    logger = get_logger()

    logger.info(f"Retrieving .csv files from {folder_path}")

    try:
        files = glob.glob(folder_path + "*.csv")
    except Exception as err:
        logger.critical(f"Error when retrieving .csv files {err}")
        quit()

    for file in files:
        insert_csv_to_db_manually(file)


def extract_file_names_from_interval(interval_str):
    interval_split = interval_str.split('::')
    date_begin = f"aisdk-{interval_split[0]}.zip"
    date_end = f"aisdk-{interval_split[2]}.zip"

    return [date_begin, date_end]

def download_interval(date_interval):
    date_interval_files = extract_file_names_from_interval(date_interval)
    start(date_interval_files)

def delete_all_entries_in_log():
    logger = get_logger()
    try:
        with open(LOG_FILE_PATH, 'r+') as log_file:
            log_file.truncate(0)
            logger.info("Successfully deleted all entries in log file")
    except IOError as e:
        logger.critical(f"IO error when accessing log file at {LOG_FILE_PATH}, error: {e}")
    except Exception as e:
        logger.critical(f"Something went wrong when accessing log file at {LOG_FILE_PATH}, error: {e}, error type: {type(e)}")


def download_all():
    delete_all_entries_in_log()
    start(all=True)


def begin(interval_to_download = None, file_to_download = None, all = False, cont = False):
    if all:
        download_all()
    elif cont:
        start(cont=True)
    elif interval_to_download is not None:
        download_interval(interval_to_download)
    elif file_to_download is not None:
        start(file_to_download)
    else:
        print("Something went wrong when determining to download an interval, specific, all or continue.")

logger = get_logger()
dpe.create_line_strings(logger)