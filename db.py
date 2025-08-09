import mysql.connector
from config import Settings

def get_conn():
    return mysql.connector.connect(
        host=Settings.DB_HOST,
        user=Settings.DB_USER,
        password=Settings.DB_PASS,
        database=Settings.DB_NAME
    )
