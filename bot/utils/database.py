import logging
import os

import mysql.connector

logger = logging.getLogger(__name__)

_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "passwd": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": os.getenv("DB_PORT"),
}


def test_connection():
    try:
        mysql.connector.connect(**_CONFIG)
        logger.info(f"Succesfully connected to database {_CONFIG['database']}")
    except mysql.connector.Error as error:
        logger.error(f"Invalid password, connection denied \n{error}")
        return False
    return True


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
            logger.error(f"SQL request {sql} failed: {error}\n")

        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
    return None
