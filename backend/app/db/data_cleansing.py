import os
import logging
from dotenv import load_dotenv
import pandas as pd
import pandas.io.sql as psql
from sqlalchemy import create_engine

ERROR_LOG_FILE_PATH = "C:\\Users\\Kristian\\Desktop\\error_log.txt"


load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
HOST_DB = os.getenv('HOST_DB')
DB_NAME = os.getenv('DB_NAME')

# chunk size to load in (we do not have enough memory to load in everything at once)
chunk_size = 1000000

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

# establish connection to database
logger = get_logger()

db_string = f"postgresql://{USER}:{PASS}@{HOST_DB}/{DB_NAME}"
engine = create_engine(db_string)


sql_query = "SELECT " \
            "(timestamp, mobile_type, mmsi, latitude, longitude, navigational_status, rot, sog, cog, heading, imo, callsign, name, ship_type, cargo_Type, width, length, type_of_position_fixing_device, draught, destination, eta, data_source_type) " \
            "FROM raw_data " \
            "WHERE "\
                "(mobile_type = 'Class A') AND "\
                "(latitude >= 54.5 AND latitude <= 58.5) AND "\
                "(longitude >= 3.2 AND longitude <= 16.5) AND "\
                "(heading >= 0 AND heading <= 359) AND "\
                "(rot >=0 AND rot <= 720) AND" \
                "(sog >= 0 AND sog <= 102)"

for data in pd.read_sql_query(sql_query, engine, chunksize=10):
    quit()


logger.info("Done!")
