from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests
import zipfile
import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')

html = urlopen("https://web.ais.dk/aisdata/")
soup = BeautifulSoup(html, 'html.parser')

results = []
dates = []

for link in soup.find_all('a', href = True):
    if "aisdk" in link.string:
        results.append(link.string)
        dates.append(link.string.split("aisdk-")[1].split(".zip")[0])

def download_files(dest_dir, log_file_name, error_log_file_name):
    path_log = dest_dir + log_file_name
    path_error_log = dest_dir + error_log_file_name 

    try:
        flog = open(path_log,'a+')
        flog.seek(0)
        data = flog.read().split('\n')

        elog = open(path_error_log, 'a')
        elog.seek(0)
    except Exception as err:
        print("Could not open log/error log file", err, type(err))
        now = datetime.now().strftime("%Y%M%D %H:%M:%S")
        elog.write("Time:", now, "Error:", err, "Error type:", type(err) + "\n")
        quit()


    if len(data) <= 0:
        print("Log file is empty, please insert the name of the latest downloaded ais file.")
        quit()

    if data[-1] in '':
        current_latest_entry = data[-2]
    else:
        current_latest_entry = data[-1]

    print("Latest entry is:", current_latest_entry)

    latest_index = results.index(current_latest_entry)
    len_results = len(results)
    
    if latest_index + 1 == len_results:
        print("No new entries available. Quitting....")
        quit()
    
    print("There are", (len_results - 1) - latest_index, "new entries available.")

    for entry in range(latest_index + 1, len_results):
        print("Trying to download file '" + results[entry] + "'...")
        
        try:
            download_result = requests.get("https://web.ais.dk/aisdata/" + results[entry], allow_redirects=True)
            path_zip = dest_dir +  "/" + results[entry]

            open(path_zip,'wb').write(download_result.content)
            print("Download successfull, extracting file ...")

            with zipfile.ZipFile(path_zip, 'r') as zip_ref:
                zip_ref.extractall(dest_dir)

            print("File has been extraced, deleting .zip file...")
            os.remove(path_zip)

            #flog.write(results[entry] + "\n")

            print(".zip file deleted.")

        except Exception as err:
            print("Something went wrong when downloading/extracting the lastest data:", err, type(err))
            now = datetime.now().strftime("%Y%M%D %H:%M:%S")
            elog.write("Time:", now, "Error:", err, "Error type:", type(err) + "\n")
            quit()

        
        print("Inserting", results[entry], "into the DB...")
        insert_into_db(dest_dir + results[entry].replace('.zip','.csv'), results[entry], flog, elog)


def insert_into_db(path_csv, name, flog, elog):
    print("Inserting csv file into raw db...")

    try:
        conn = psycopg2.connect(database="ais", user=USER, password=PASS, host="postgres://db", port="5432")
        conn.autocommit = True
        cursor = conn.cursor()
    except Exception as err:
        print("Could not connect to the database:", err, "error type:", type(err))
        now = datetime.now().strftime("%Y%M%D %H:%M:%S")
        elog.write("Time:", now, "Error:", err, "Error type:", type(err)+"\n")
        quit()

    sql = "COPY raw_data FROM STDIN WITH (format csv, delimiter E'\u002C', header true)"

    try:
        file = open(path_csv, 'r')
    except FileNotFoundError:
        print("CSV-file not found at path:", path_csv)
        quit()
    except Exception as err:
        print("Something went wrong when opening the csv file at:", path_csv, "Error:", err, "Error type:", type(err))
        now = datetime.now().strftime("%Y%M%D %H:%M:%S")
        elog.write("Time:", now, "Error:", err, "Error type:", type(err) + "\n")
        quit()

    try:
        cursor.copy_expert(sql, file)
        file.close()
        conn.commit()
        conn.close()
    except Exception as err:
        print("Something went wrong when inserting into the database:", err, "error type:", type(err))
        now = datetime.now().strftime("%Y%M%D %H:%M:%S")
        elog.write("Time:", now, "Error:", err, "Error type:", type(err) + "\n")
        quit()

    flog.write(name + "\n")

    print("Insertion completed succesfully!")

download_files("/srv/data/csv/", "log.txt", "error_log.txt")