import logging
import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "passwd": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": os.getenv("DB_PORT"),
}


def test_connection():

    with mysql.connector.connect(**_CONFIG):
        try:
            logging.info(f"Succesfully connected to database {_CONFIG['database']}")
            return True
        except mysql.connector.Error:
            logging.warning("Invalid password, connection denied")
    return False


def execute(sql, data=None, dictionary=False, fetchone=False, fetchall=False):
    with mysql.connector.connect(**_CONFIG) as cnx:
        cursor = cnx.cursor(dictionary=dictionary, buffered=True)
        try:
            if data:  # parametrized query
                cursor.execute(sql, data)
            else:
                cursor.execute(sql)
            cnx.commit()
        except mysql.connector.Error as error:
            logging.error(f"SQL request {sql} failed: {error}\n")

        if fetchone:
            return cursor.fetchone()
        elif fetchall:
            return cursor.fetchall()
