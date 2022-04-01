from dotenv import load_dotenv
import os
import glob
import pandas as pd
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests
import zipfile, rarfile
from backend.app.ais_data_handling.data_insertion import insert_cleansed_data, insert_into_star
from backend.app.ais_data_handling.douglas_peucker import create_line_strings

from backend.app.ais_data_handling.trips_partitioning import get_cleansed_data

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH')
ERROR_LOG_FILE_PATH = os.getenv('ERROR_LOG_FILE_PATH')
CSV_FILES_PATH = os.getenv('CSV_FILES_PATH')
HOST_DB = os.getenv('HOST_DB')

def get_downloaded_csv_files_from_folder(logger):
    """
    Gets the .csv files located in the specified folder.
    :param logger: A logger used for logging errors/warnings.
    :return: A list of file names.
    """
    logger.info(f"Retrieving .csv files from {CSV_FILES_PATH}")
    file_names = []
    try:
        file_paths = glob.glob(CSV_FILES_PATH + "*.csv")
    except Exception as err:
        logger.warning("No .csv files in {CSV_FILES_PATH}")
        file_paths = []
    finally:
        if len(file_paths) > 0:
            for file in file_paths:
                file_paths.append(file.split(CSV_FILES_PATH)[-1])
    
    return file_paths


def get_csv_files_from_log(logger):
    """
    Gets the .csv files from the log. The .csv files in the log have all been processed and are already insereted into the database.
    :param logger: A logger used for logging errors/warnings.
    :return: A list of .csv file names.
    """
    try:
        flog = open(LOG_FILE_PATH,'a+')
        flog.seek(0)
        csv_file_list = flog.read().split('\n')
    except Exception as err:
        logger.error(f"Error when opening log file: {err} type: {type(err)}. Qutting.")
        quit()
    finally:
        flog.close()

    return csv_file_list

def connect_to_to_ais_web_server_and_get_data(logger):
    """
    Connects to the ais web server and gets the .csv files (ais data) located there.
    :param logger: A logger for loggin warning/errors
    :return: A list with the names of the .zip/.rar files available for download on the web server. Example: 'aisdk-2022-01-01.zip'
    """
    try:
        html = urlopen("https://web.ais.dk/aisdata/")
    except HTTPError as e:
        logger.error(f"HTTP error: {e.code}. Site may be down, quitting program")
        quit()
    except URLError as e:
        logger.error(f"Url-error: {e.reason}")
        quit()
    else:
        logger.info("Succesfully connected to website")

    soup = BeautifulSoup(html, 'html.parser')
    results = []

    for link in soup.find_all('a', href = True):
        if "aisdk" in link.string:
            results.append(link.string)

    return results

def download_file_from_ais_web_server(file_name, logger):
    """
    Downloads a specified file from the webserver into the CSV_FILES_FOLDER.
    It will also unzip it, as well as delete the compressed file afterwards.
    :param file_name: The file to be downloaded. Example 'aisdk-2022-01-01.zip'
    :param logger: A logger to log warnings/errors.
    """
    logger.info(f"Trying to download file '{file_name}'")
    try:
        download_result = requests.get("https://web.ais.dk/aisdata/" + file_name, allow_redirects=True)
        download_result.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        logger.warning(f"Received HTTP error {http_err} when trying to download file {file_name}. Skipping this file.")
    except requests.exceptions.ConnectionError as conn_err:
        logger.critical(f"Could not connect to web-server to download file {file_name}. Received connection error: {conn_err}. Qutting..")
        quit()
    except requests.exceptions.Timeout as time_err:
        logger.warning(f"We timed out when trying to download file {file_name}. Error: {time_err}. Skipping this file.")
    except requests.exceptions.RequestException as re_error:
        logger.warning(f"Something went wrong when requesting to download file {file_name}. Error: {re_error}. Skipping this file.")


    path_to_compressed_file = CSV_FILES_PATH + file_name
    
    try:
        f = open(path_to_compressed_file,'wb')
        f.write(download_result.content)
        logger.info("Download successful, extracting file.")
    except Exception as e:
        logger.warning(f"Could not save file at {path_to_compressed_file}. Error: {e}")
    finally:
        f.close()
    
    try:
        if ".zip" in path_to_compressed_file: 
            with zipfile.ZipFile(path_to_compressed_file, 'r') as zip_ref:
                zip_ref.extractall(CSV_FILES_PATH)
        elif ".rar" in path_to_compressed_file:
            with rarfile.RarFile(path_to_compressed_file) as rar_ref:
                rar_ref.extractall(path=CSV_FILES_PATH)
        else:
            logger.warning("Could not extract file at {path_zip}. Unsupported file format (not .zip or .rar). Skipping this file!")
            
        logger.info("File has been extraced, deleting compressed file")
        os.remove(path_to_compressed_file)
        logger.info("Compressed file deleted")

    except Exception as err:
        logger.critical(f"Something went wrong when extracting the file: {err}, type: {type(err)}")
        quit()

def add_new_file_to_log(file_name, logger):
    """
    Adds the specificed file to the log.
    The .env variable LOG_FILE_PATH must be specified.
    :param file_name: The file name of the .csv file that has been processeded. Example: "aisdk-2022-01-01.csv"
    :praram logger: A logger used for warnings/errors.
    """
    logger.info(f"Adding {file_name} to log file")
    try:
        with open(LOG_FILE_PATH, 'a+') as log_file:
            log_file.seek(0)
            data = log_file.read()
            if len(data) > 0:
                log_file.write("\n")
            log_file.write(file_name)
            logger.info(f"Successfully added {file_name} to log.")
    except IOError as e:
        logger.critical(f"IO error when accessing log file at {LOG_FILE_PATH}, error: {e}")
    except Exception as e:
        logger.critical(f"Something went wrong when accessing log file at {LOG_FILE_PATH}, error: {e}, error type: {type(e)}")

def cleanse_csv_file_and_convert_to_df(file_name):
    """
    Takes a .csv file and cleanses it according to the set predicates.
    :param file_name: File name to cleanse. Example: 'aisdk-2022-01-01.csv'
    :return: A cleansed dataframe, sorted by timestamp (ascending)
    """
    df = pd.read_csv(CSV_FILES_PATH + file_name, na_values=['Unknown','Undefined'])
    df = df.drop(['A','B','C','D','Destination','ETA','Cargo type','Data source type'],axis=1)
    
    # Remove all the rows which does not satisfy our conditions
    df['# Timestamp'] = pd.to_datetime(df['# Timestamp'], format="%d/%m/%Y %H:%M:%S")
    df['Latitude'] = df['Latitude'].round(4)
    df['Longitude'] = df['Longitude'].round(4)
    df = df[
            (df["Type of mobile"] != "Class B") &
            (df["MMSI"].notna()) &
            (df["MMSI"].notnull()) &
            (df['Latitude'] >=53.5) & (df['Latitude'] <=58.5) &
            (df['Longitude'] >= 3.2) & (df['Longitude'] <=16.5) &
            (df['SOG'] >= 0) & (df['SOG'] <=102)
           ].reset_index()
    df = df.sort_values(by=['# Timestamp'], ignore_index=True)

    return df

def check_if_csv_is_in_log(logger):
    """
    Checks if all the downloaded .csv files are also present in the log file.
    If they are not, it will run them through the pipeline and add it to the logs.
    :param logger: A logger to log warning/errors.
    """

    csv_files_log = get_csv_files_from_log()
    downloaded_csv_files = get_downloaded_csv_files_from_folder()

    # Check if the downloaded .csv files are also present in the logs.
    # If they are not present in the logs, it will add the .csv files
    # to the database and to the log.
    for downloaded_csv in downloaded_csv_files:
        if downloaded_csv not in csv_files_log:
            df = cleanse_csv_file_and_convert_to_df(downloaded_csv)
            partition_trips_and_insert(file_name=downloaded_csv, df=df, logger=logger)


def continue_from_log(logger):
    logger.info("Continuing from the log file.")

    check_if_csv_is_in_log()

    # Continue from log now.
    latest_csv_file = get_csv_files_from_log()[-1]
    files_on_server = connect_to_to_ais_web_server_and_get_data()

    # Take the latest .csv file from the log and continues from there.
    try:
        latest_file_index = files_on_server.index(latest_csv_file)
    except ValueError as ve:
        logger.critical("Could not find {latest_csv_file} on the ais web server. Quitting.")
        quit()

    files_to_download = files_on_server[latest_file_index + 1, -1]

    for file in files_to_download:
        download_cleanse_insert(file)

def download_cleanse_insert(file_name, logger, check_for_month_download = False):
    """
    Downloads the given file, runs it through the pipeline and adds the file to the log.
    :param file_name: The file to be downloaded, cleansed and inserted
    :param logger: A logger for logging warning/errors.
    """
    download_file_from_ais_web_server(file_name, logger)

    if(check_for_month_download):
        check_if_csv_is_in_log()
        return

    df = cleanse_csv_file_and_convert_to_df(file_name)
    partition_trips_and_insert(file_name, df, logger)

def partition_trips_and_insert(file_name, df, logger):
    """
    Takes a dataframe and runs it through the pipeline (trips partitioning, cleansing) and inserts it into the star schema.
    It will also add the file to the log.
    :param df: The dataframe to insert
    :param file_name: The .csv file name to add to the log.
    """
    trip_list = get_cleansed_data(df, logger)
    trip_list = create_line_strings(trip_list, logger)
    insert_cleansed_data(trip_list, logger)
    insert_into_star(logger)
    add_new_file_to_log(file_name)

def download_all_and_process_everything(logger):
    files_to_download_and_process = connect_to_to_ais_web_server_and_get_data()
    for file in files_to_download_and_process:
        if(file.split('-') <= 3):
            download_cleanse_insert(file_name=file, logger=logger, check_for_month_download=True)
        else:
            download_cleanse_insert(file_name=file, logger=logger, check_for_month_download=False)

def download_interval(interval, logger):
    dates = interval.split('::')
    csv_files_on_server = connect_to_to_ais_web_server_and_get_data()

    for csv_file in csv_files_on_server:
        if dates[0] in csv_file:
            begin_index = csv_files_on_server.index(csv_file)
            continue
        if dates[1] in csv_file:
            end_index = csv_files_on_server.index(csv_file)
    
    if begin_index is None or end_index is None:
        logger.critical("The files on the webserver does not contain the interval you're trying to download. Qutting.")
        quit()

    files_to_download = csv_files_on_server[begin_index,end_index]

    for file in files_to_download:
        if(file.split('-') <= 3):
            download_cleanse_insert(file, check_for_month_download=True)
        else:
            download_cleanse_insert(file, check_for_month_download=False)


def begin(logger, interval_to_download = None, file_to_download = None, all = False, cont = False):
    if all:
        download_all_and_process_everything(logger)
    elif cont:
        continue_from_log(logger)
    elif interval_to_download is not None:
        download_interval(interval_to_download, logger)
    elif file_to_download is not None:
        download_cleanse_insert(file_to_download, check_for_month_download=True)

