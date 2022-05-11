import datetime
from dotenv import load_dotenv
import os
import glob
import pandas as pd
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests
import zipfile, rarfile
from data_insertion import calculate_date_tim_dim_and_hex, insert_into_star
from trips_partitioning import get_cleansed_data
import geopandas as gpd
import numpy as np
import csv

load_dotenv()
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH')
ERROR_LOG_FILE_PATH = os.getenv('ERROR_LOG_FILE_PATH')
CSV_FILES_PATH = os.getenv('CSV_FILES_PATH')

time_cleansing_begin = datetime.datetime.now()

def get_downloaded_csv_files_from_folder(logger, month_file_name = None):
    """
    Gets the .csv files located in the specified folder.
    :param logger: A logger used for logging errors/warnings.
    :param month_file_name: To only look for the .csv file from a specific month of a specific year. Example: 'aisdk-2022-01' will return the paths to all the .zip files from that month.
    :return: A list of file names.
    """
    logger.info(f"Retrieving .csv files from {CSV_FILES_PATH}")
    file_names = []
    try:
        if month_file_name is not None:
            file_paths = glob.glob(CSV_FILES_PATH + month_file_name + "*.csv")
        else:
            file_paths = glob.glob(CSV_FILES_PATH + "*.csv")
    except Exception as err:
        logger.warning(f"No .csv files in {CSV_FILES_PATH}")
        file_paths = []
    finally:
        if len(file_paths) > 0:
            for file in file_paths:
                file_names.append(file.split(CSV_FILES_PATH)[-1])
    
    return sorted(file_names)

def get_csv_files_from_log(logger):
    """
    Gets the .csv files from the log. The .csv files in the log have all been processed and are already insereted into the database.
    :param logger: A logger used for logging errors/warnings.
    :return: A list of .csv file names, sorted by date, in reverse order (latest last)
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

    return sorted(csv_file_list)

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

def download_file_from_ais_web_server(file_name: str, logger):
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

def add_new_file_to_log(file_name: str, logger):
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

def cleanse_csv_file_and_convert_to_df(file_name: str, logger):
    """
    Takes a .csv file and cleanses it according to the set predicates.
    :param file_name: File name to cleanse. Example: 'aisdk-2022-01-01.csv'
    :return: A cleansed geodataframe, sorted by timestamp (ascending)
    """
    DATA = []
    DATA.append(file_name)

    types = {
        '# Timestamp': str,
        'Type of mobile': str,
        'MMSI': 'Int32',
        'Navigational status': str,
        'Heading': 'Int16',
        'IMO': 'Int32',
        'Callsign': str,
        'Name': str,
        'Ship type': str,
        'Cargo type': str,
        'Width': 'Int32',
        'Length': 'Int32',
        'Type of position fixing device': str,
        'Destination': str,
        'ETA': str,
        'Data source type': str,
    }
    logger.info(f"Loading, converting and cleansing {file_name}")
    df = pd.read_csv(CSV_FILES_PATH + file_name, parse_dates=['# Timestamp'], na_values=['Unknown','Undefined'], dtype=types)
    DATA.append(len(df))

    # Remove unwanted columns containing data we do not need. This saves a little bit of memory.
    # errors='ignore' is sat because older ais data files may not contain these columns.
    time_cleansing_begin = datetime.datetime.now()
    df = df.drop(['A','B','C','D','ETA','Cargo type','Data source type'],axis=1, errors='ignore')
    
    df['# Timestamp'] = pd.to_datetime(df['# Timestamp'], format="%d/%m/%Y %H:%M:%S", errors="coerce")

    # Remove all the rows which does not satisfy our conditions
    df = df[
            (df["Type of mobile"] != "Class B") &
            (df["MMSI"].notna()) &
            (df["MMSI"].notnull()) &
            (df['# Timestamp'].notnull()) &
            (df['Latitude'] >=53.5) & (df['Latitude'] <=58.5) &
            (df['Longitude'] >= 3.2) & (df['Longitude'] <=16.5) &
            (df['SOG'] >= 0.1) & (df['SOG'] <=102)
           ].reset_index()
    DATA.append(len(df))

    HEADER = [file_name,'Total_rows_in_csv', 'rows_after_filter']

    with open(CSV_FILES_PATH + file_name + '_stats_1.csv', 'w', encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerow(DATA)

    # We round the lat and longs as we do not need 15 decimals of precision
    # This will save some computation time later.
    # We also round rot, sog and cog, as we do not need a lot of decimal precision here
    df['Latitude'] = np.round(df['Latitude'], decimals=4)
    df['Longitude'] = np.round(df['Longitude'], decimals=4)
    df['ROT'] = np.round(df['ROT'], decimals=2)
    df['SOG'] = np.round(df['SOG'], decimals=2)
    df['COG'] = np.round(df['COG'], decimals=2)

    # Rename the columns
    df = df.rename(columns={
            '# Timestamp':'timestamp',
            'Type of mobile':'type_of_mobile',
            'Navigational status':'navigational_status',
            'Ship type':'ship_type',
            'Type of position fixing device':'type_of_position_fixing_device',
        })
    
    # lower case names in the columns
    df.columns = map(str.lower, df.columns)

    # Convert to geopandas dataframe
    # We use 'EPSG:4326' as this is what we recieve from the AIS site
    # However, we convert it to 3857, such that we can use it calculate distances in meters
    df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['longitude'], df['latitude']), crs="EPSG:4326")
    df = df.drop(columns=['index','latitude','longitude'], errors='ignore')
    df = df.to_crs(epsg="3857")

    return df

def check_if_csv_is_in_log(logger):
    """
    Checks if all the downloaded .csv files are also present in the log file.
    If they are not, it will run them through the pipeline and update the log.
    :param logger: A logger to log warning/errors.
    """

    csv_files_log = get_csv_files_from_log(logger)
    downloaded_csv_files = get_downloaded_csv_files_from_folder(logger)

    # Check if the downloaded .csv files are also present in the logs.
    # If they are not present in the logs, it will add the .csv files
    # to the database and to the log.
    for downloaded_csv in downloaded_csv_files:
        if downloaded_csv not in csv_files_log:
            df = cleanse_csv_file_and_convert_to_df(downloaded_csv, logger=logger)
            partition_trips_and_insert(file_name=downloaded_csv, df=df, logger=logger)

def continue_from_log(logger):
    logger.info("Continuing from the log file.")
    
    # First we check if we have any .csv files downloaded, that have not yet been inserted
    check_if_csv_is_in_log(logger)

    # Continue from log
    latest_csv_file = get_csv_files_from_log(logger)[-1]
    files_on_server = connect_to_to_ais_web_server_and_get_data(logger)

    # Take the latest .csv file from the log and continues from there.
    try:
        latest_file_index = files_on_server.index(latest_csv_file)
    except ValueError as ve:
        logger.critical("Could not find {latest_csv_file} on the ais web server. Quitting.")
        quit()

    files_to_download = files_on_server[latest_file_index + 1: -1]
    logger.info(f"There are {len(files_to_download)} compressed files to download.")

    file: str
    for file in files_to_download:
        download_cleanse_insert(file_name=file, logger=logger)

def does_file_contain_whole_month(file_name: str):
    """
    Checks if the file contains a whole month.
    E.g., a file name with the name 'aisdk-2022-01.zip' will contain data for the whole month of January
    :param file_name: The file name to check. Example: 'aisdk-2022-01.zip will return True, 'aisdk-2022-01-01.zip' will return False.
    :return: True | False
    """
    # This should probably be done with strftime instead
    # See https://www.programiz.com/python-programming/datetime/strftime
    length_split = len(file_name.split('-'))
    if(length_split <= 3):
        return True
    else:
        return False

def download_cleanse_insert(file_name: str, logger):
    """
    Downloads the given file, runs it through the pipeline and adds the file to the log.
    :param file_name: The file to be downloaded, cleansed and inserted
    :param logger: A logger for logging warning/errors.
    """
    download_file_from_ais_web_server(file_name, logger)

    if(does_file_contain_whole_month(file_name)):
        files_to_insert = get_downloaded_csv_files_from_folder(file_name, logger=logger)

    files_to_insert = []
    if len(files_to_insert) <= 0:
        files_to_insert.append(file_name)
    
    for file in files_to_insert:
        file_name = file
        if ".zip" in file: 
            file_name = file.replace('.zip', '.csv')
        else:
            file_name = file.replace('.rar', '.csv')
        df = cleanse_csv_file_and_convert_to_df(file_name=file_name, logger=logger)
        partition_trips_and_insert(file, df, logger)

def partition_trips_and_insert(file_name: str, df: gpd.GeoDataFrame, logger):
    """
    Takes a dataframe and runs it through the pipeline (trips partitioning, cleansing) and inserts it into the star schema.
    It will also add the file to the log.
    :param df: The dataframe to insert
    :param file_name: The .csv file name to add to the log.
    """
    
    df_cleansed = get_cleansed_data(df, logger, file_name)

    df_cleansed = df_cleansed.to_crs(epsg="4326")
    df_cleansed = df_cleansed.rename_geometry('location')
    df_cleansed = df_cleansed.drop(['point'],axis=1, errors='ignore')

    time_cleansing_end = datetime.datetime.now()
    time_delta = time_cleansing_end - time_cleansing_begin
    cleansing_time_taken = str(time_delta.total_seconds() / 60)

    df_cleansed = calculate_date_tim_dim_and_hex(df_cleansed, logger)
    insert_into_star(df_cleansed, logger, file_name, cleansing_time_taken)
    add_new_file_to_log(file_name, logger=logger)


def download_all_and_process_everything(logger):
    """
    Downloads everything available on the ais web site and runs it through the pipeline.
    :param logger: A logger used for logging errors/warnings.
    """
    logger.info("Downloading and processing EVERYTHING.")
    files_to_download_and_process = connect_to_to_ais_web_server_and_get_data(logger)
    logger.info(f"There are in total {files_to_download_and_process} compressed files to download and process.")
    for file in files_to_download_and_process:
        download_cleanse_insert(file_name=file, logger=logger)

def download_interval(interval: str, logger):
    """
    Downloads and processes all the available ais data in the given interval.
    :param interval: The interval (date) to download and process.
    """
    dates = interval.split('::')
    csv_files_on_server = connect_to_to_ais_web_server_and_get_data(logger)
    begin_index = None
    end_index = None
    for csv_file in csv_files_on_server:
        if begin_index is None:
            if dates[0] in csv_file:
                begin_index = csv_files_on_server.index(csv_file)
                continue
        if end_index is None:
            if dates[1] in csv_file:
                end_index = csv_files_on_server.index(csv_file)
    
    if begin_index is None or end_index is None:
        logger.critical("The files on the webserver does not contain the interval you're trying to download. Qutting.")
        quit()

    files_to_download = csv_files_on_server[begin_index:end_index]

    logger.info(f"There are in total {len(files_to_download)} compressed files to download and process.")

    file: str
    for file in files_to_download:
        download_cleanse_insert(file_name=file, logger=logger)

def start(logger, interval_to_download = None, file_to_download = None, all = False, cont = False, only_from_folder = False):
    """
    Main function of the module. Used to start the download and processesing process.
    :param logger: A logger used for logging warnings/errors.
    :param interval_to_download: The interval to download and process. Default is 'None'
    :param file_to_download: A specific file to download and proces. Default is 'None'
    :param all: If True, will download and process all avaiable ais data. Default is 'False'
    :param cont: If True, will continue to download and process data from the latest file entry of the log file. Default is 'False'
    :param only_from_folder: Will only process and insert data from a folder. Default is 'False'
    """
    time_begin = datetime.datetime.now()
    if all:
        download_all_and_process_everything(logger)
    elif cont:
        continue_from_log(logger)
    elif interval_to_download is not None:
        download_interval(interval_to_download, logger)
    elif file_to_download is not None:
        download_cleanse_insert(file_to_download, logger)
    elif only_from_folder is not None:
        check_if_csv_is_in_log(logger)
    
    time_end = datetime.datetime.now()
    time_delta = time_end - time_begin
    print("Time end: " + time_end.strftime("%d%m%Y, %H:%M%S"))
    print(f"Took approx: {time_delta.total_seconds() / 60} minutes")