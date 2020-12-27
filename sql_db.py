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


def create_database(config):
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
    with OpenDatabase(config) as cursor:
        sql = """
            CREATE TABLE IF NOT EXISTS to_search (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                string_search VARCHAR(255) DEFAULT '',
                region VARCHAR(150) DEFAULT '',
                city VARCHAR(30) DEFAULT '',
                street VARCHAR(50) DEFAULT '',
                house VARCHAR(3) DEFAULT '',
                try INT NOT NULL DEFAULT 1
                );
            """
        cursor.execute(sql)

        sql = """
            CREATE TABLE IF NOT EXISTS results_search (
                object_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                kad_number VARCHAR(25) NOT NULL,
                address VARCHAR(255) DEFAULT '',
                link VARCHAR(55) NOT NULL,
                floor VARCHAR(3),
                area DEC(8,2),
                geo VARCHAR(26),
                region VARCHAR(150) DEFAULT '',
                city VARCHAR(30) DEFAULT '',
                street VARCHAR(50) DEFAULT '',
                house VARCHAR(3) DEFAULT '',
                apartment VARCHAR(4) DEFAULT '',	
                json_main LONGTEXT,
                json_extra LONGTEXT
                );
            """
        cursor.execute(sql)

        sql = """
            CREATE TABLE IF NOT EXISTS not_found (
                num_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                id INT NOT NULL
                );
            """
        cursor.execute(sql)

        sql = """
            CREATE TABLE IF NOT EXISTS resume (
                search_num INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                found INT NOT NULL,
                not_found INT NOT NULL,
                equal INT NOT NULL
                );
            """
        cursor.execute(sql)

        sql = """
            CREATE TRIGGER OnInsertNotFound
                AFTER INSERT ON not_found
                FOR EACH ROW
                BEGIN
                    SET @id = NEW.id;
                    UPDATE to_search SET try = try + 1 WHERE id = @id;
                    IF (SELECT try FROM to_search WHERE id = @id) = 3 THEN
                        DELETE FROM to_search WHERE id = @id;
                    END IF;
                END;
            """
        cursor.execute(sql)


if __name__ == '__main__':
    create_database(db_config)
    create_tables(db_config)
    print('All done')
