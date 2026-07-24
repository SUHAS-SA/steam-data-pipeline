import os
import glob
import psycopg2
from src import config

class DatabaseLoader:
    """Connects to PostgreSQL database and loads generated SQL dumps safely."""

    def __init__(self, db_name=None, db_user=None, db_pass=None, db_host=None, db_port=None, sql_dir=None):
        self.db_name = db_name or config.DB_NAME
        self.db_user = db_user or config.DB_USER
        self.db_pass = db_pass or config.DB_PASS
        self.db_host = db_host or config.DB_HOST
        self.db_port = db_port or config.DB_PORT
        self.sql_dir = sql_dir or config.SQL_DIR

    def get_connection(self):
        return psycopg2.connect(
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_pass,
            host=self.db_host,
            port=self.db_port
        )

    def load_sql_files(self):
        if not os.path.exists(self.sql_dir):
            print(f"Error: SQL directory not found at {self.sql_dir}")
            return False

        sql_files = glob.glob(os.path.join(self.sql_dir, "*.sql"))
        if not sql_files:
            print(f"No SQL files found to load in {self.sql_dir}")
            return False

        sql_files.sort()
        print(f"Connecting to database '{self.db_name}' at {self.db_host}:{self.db_port}...")

        try:
            conn = self.get_connection()
            conn.autocommit = True
            cursor = conn.cursor()
            print("Connected successfully to PostgreSQL database.")
        except Exception as e:
            print(f"[CRITICAL ERROR] Failed to connect to PostgreSQL: {e}")
            return False

        successful = 0
        failed = 0

        for i, sql_file in enumerate(sql_files, 1):
            filename = os.path.basename(sql_file)
            print(f"[{i}/{len(sql_files)}] Importing {filename}...")

            try:
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()

                cursor.execute(sql_content)
                print(f"  -> Successfully imported {filename}")
                successful += 1
            except Exception as e:
                print(f"  -> [ERROR] Failed to import {filename}: {e}")
                failed += 1

        cursor.close()
        conn.close()

        print("\n=== Database Load Summary ===")
        print(f"Successfully imported files: {successful}")
        print(f"Failed file imports:       {failed}")

        return failed == 0

if __name__ == "__main__":
    loader = DatabaseLoader()
    loader.load_sql_files()
