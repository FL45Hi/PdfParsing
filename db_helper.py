from configparser import ConfigParser
import psycopg2
import psycopg2.extras as psql_extras
import pandas as pd
from typing import Dict
import os

class DBHelper():
    def __init__(self, pdf_name) -> None:
        self.databaseName = pdf_name
        self.texts_sql = """
            CREATE TABLE texts (
                id SERIAL,
                page_num SERIAL PRIMARY KEY,
                txts TEXT NOT NULL
            )
        """
        self.images_sql = """
            CREATE TABLE images (
                id SERIAL,
                fk_page_num SERIAL REFERENCES texts(page_num),
                images_bb BYTEA 
            )
        """

    def load_connection_info(self, ini_filename: str) -> Dict[str, str]:
        parser = ConfigParser()
        parser.read(ini_filename)
        parser.set('postgresql', 'database', self.databaseName)

        with open(ini_filename, 'w+') as configfile:
            parser.write(configfile, space_around_delimiters=False)

        # Create a dictionary of the variables stored under the "postgresql" section of the .ini
        conn_info = {param[0]: param[1] for param in parser.items("postgresql")}
        return conn_info


    def create_db(self, conn_info: Dict[str, str], ) -> None:
        # Connect just to PostgreSQL with the user loaded from the .ini file
        psql_connection_string = f"user={conn_info['user']} password={conn_info['password']}"
        conn = psycopg2.connect(psql_connection_string)
        cur = conn.cursor()

        # "CREATE DATABASE" requires automatic commits
        conn.autocommit = True
        # cur.execute(f"revoke connect on database {str(self.databaseName).lower()} FROM PUBLIC")
        cur.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid() AND datname = '{str(self.databaseName).lower()}';")
        droping_database_query = f"DROP DATABASE IF EXISTS {str(self.databaseName).lower()}"
        cur.execute(droping_database_query)

        sql_query = f"CREATE DATABASE {str(self.databaseName).lower()}"

        try:
            cur.execute(sql_query)
        except Exception as e:
            print(f"{type(e).__name__}: {e}")
            print(f"Query: {cur.query}")
            cur.close()
        else:
            # Revert autocommit settings
            conn.autocommit = False


    def create_table(
            self,
        sql_query: str, 
        conn: psycopg2.extensions.connection, 
        cur: psycopg2.extensions.cursor
    ) -> None:
        try:
            # Execute the table creation query
            cur.execute(sql_query)
        except Exception as e:
            print(f"{type(e).__name__}: {e}")
            print(f"Query: {cur.query}")
            conn.rollback()
            cur.close()
        else:
            # To take effect, changes need be committed to the database
            conn.commit()

    def create_table_schema(
            self,
        conn: psycopg2.extensions.connection, 
        cur: psycopg2.extensions.cursor
    ) -> None:  
        self.create_table(self.texts_sql, conn, cur)
        self.create_table(self.images_sql, conn, cur)


    def insert_data(
            self,
        query: str,
        conn: psycopg2.extensions.connection,
        cur: psycopg2.extensions.cursor,
        df: pd.DataFrame,
        page_size: int
    ) -> None:
        data_tuples = [tuple(row.to_numpy()) for index, row in df.iterrows()]

        try:
            psql_extras.execute_values(
                cur, query, data_tuples, page_size=page_size)
            # print("Query:", cur.query)

        except Exception as error:
            print(f"{type(error).__name__}: {error}")
            print("Query:", cur.query)
            conn.rollback()
            cur.close()

        else:
            conn.commit()

    def read_blob(
        self,
        conn: psycopg2.extensions.connection,
        cur: psycopg2.extensions.cursor,
    ) -> None:
        try:
            sql_query = f"SELECT images.images_bb FROM images WHERE images.id=1"
            cur.execute(sql_query)
            blob = cur.fetchone()
            with open(os.path.join("Retrieve/", "image.png") , 'wb') as image_file:
                image_file.write(blob[0])
                image_file.close()
        except Exception as e:
            print(f"{type(e).__name__}: {e}")
            conn.rollback()
            cur.close()
        else:
            conn.commit()
        

if __name__ == "__main__":
    # host, database, user, password
    conn_info = DBHelper().load_connection_info(".\db.ini")

    # Create the desired database
    DBHelper().create_db(conn_info)

    # Connect to the database created
    connection = psycopg2.connect(**conn_info)
    cursor = connection.cursor()

    # Create the "texts" table
    texts_sql = """
        CREATE TABLE texts (
            id SERIAL,
            page_num SERIAL PRIMARY KEY,
            txts TEXT NOT NULL
        )
    """
    DBHelper().create_table(texts_sql, connection, cursor)

    # Create the "images" table
    images_sql = """
        CREATE TABLE images (
            id SERIAL,
            fk_page_num SERIAL REFERENCES texts(page_num),
            images_bb BYTEA 
        )
    """
    DBHelper().create_table(images_sql, connection, cursor)

    # Insert data into the "texts" table
    texts_df = pd.DataFrame({
        "page_num": [1, 2, 3], 
        "txts": ["Street MGS, 23", "Street JHPB, 44", "Street DS, 76"]
    })
    texts_query = "INSERT INTO texts(page_num, txts) VALUES %s"
    DBHelper().insert_data(texts_query, connection, cursor, texts_df, 100)

    # Insert data into the "images" table
    images_df = pd.DataFrame({
        "fk_page_num": [1, 2, 2], 
        "images_bb": ["Michaelfnn", "Jimdr", "Pamrrr"], 
    })
    images_query = "INSERT INTO images(fk_page_num, images_bb) VALUES %s"
    DBHelper().insert_data(images_query, connection, cursor, images_df, 100)

    # Close all connections to the database
    connection.close()
    cursor.close()