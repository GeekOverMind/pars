#!/usr/bin/python3.9

import mysql.connector


db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'qpwo',
    'database': 'egrp365'
    }


class OpenDatabase:
    def __init__(self, config: dict):
        self.configuration = config

    def __enter__(self):
        try:
            self.conn = mysql.connector.connect(**self.configuration)
            self.cursor = self.conn.cursor()
            return self.cursor
        except mysql.connector.errors.InterfaceError as err:
            print(f'Ошибка: {err}')
        except mysql.connector.errors.ProgrammingError as err:
            print(f'Ошибка: {err}')

    def __exit__(self, exc_type, exc_value, exc_trace):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

        if exc_type:
            with open('log_error.txt', 'a') as txt_file:
                print(f'{exc_type}: {exc_value}', file=txt_file)
