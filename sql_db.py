import mysql.connector


db_config = {
    'host': 'localhost',
    'user': 'user_pc',
    'password': '1235',
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


def create_database(config):
    """
    Creates a database
    :param config: dictionary with connection arguments for connector
    :return: nothing
    """
    new_config = config.copy()
    del new_config['database']
    with OpenDatabase(new_config) as cursor:
        sql = """
            DROP DATABASE IF EXISTS egrp365;
            """
        cursor.execute(sql)

        sql = """
            CREATE DATABASE egrp365;
            """
        cursor.execute(sql)


def create_tables(config):
    """
    Creates tables
    :param config: dictionary with connection arguments for connector
    :return: nothing
    """
    with OpenDatabase(config) as cursor:
        sql = """
            CREATE TABLE IF NOT EXISTS to_search (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                string_search VARCHAR(255) DEFAULT '',
                region VARCHAR(150) DEFAULT '',
                city VARCHAR(30) DEFAULT '',
                street VARCHAR(50) DEFAULT '',
                house VARCHAR(3) DEFAULT ''
                );
            """
        cursor.execute(sql)

        sql = """
            CREATE TABLE IF NOT EXISTS results_search (
                object_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                kad_number NOT NULL VARCHAR(20),
                address VARCHAR(255),
                href NOT NULL VARCHAR(55),
                floor VARCHAR(3),
                area DEC(8,2),
                geo VARCHAR(26),
                region VARCHAR(150),
                city VARCHAR(30),
                street VARCHAR(50),
                house VARCHAR(3),
                apartment VARCHAR(4),	
                json_main NVARCHAR(MAX),
                json_total NVARCHAR(MAX)
                );
            """
        cursor.execute(sql)

        sql = """
            CREATE TABLE IF NOT EXISTS found (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                string_search VARCHAR(255),
                );
            """
        cursor.execute(sql)

        sql = """
            CREATE TABLE IF NOT EXISTS not_found (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                string_search VARCHAR(255),
                string_search VARCHAR(255) DEFAULT '',
                region VARCHAR(150) DEFAULT '',
                city VARCHAR(30) DEFAULT '',
                street VARCHAR(50) DEFAULT '',
                house VARCHAR(3) DEFAULT ''
                );
            """
        cursor.execute(sql)

        sql = """
            CREATE TABLE IF NOT EXISTS try (
                try_num INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                
                id INT NOT NULL,
                CONSTRAINT not_found_id_fk
                FOREIGN KEY (id)
                REFERENCES not_found (id) ON DELETE CASCADE	
                );
            """
        cursor.execute(sql)
