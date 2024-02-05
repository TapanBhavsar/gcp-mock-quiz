import json
import sqlite3
import pandas as pd

class SqlConnection():
    def __init__(self, db_file, clean_start=False, check_same_thread=False) -> None:
        self.check_same_thread = check_same_thread
        self._connect_database(db_file)
        self._cursor = self._conn.cursor()
        if clean_start:
            self._clean_data()
        self._create_table()

    def __del__(self):
        if self._conn:
            self._conn.close()

    def _connect_database(self, db_file):
        self._conn = None
        try:
            self._conn = sqlite3.connect(db_file, 
                                         check_same_thread=self.check_same_thread)
        except Exception as error:
            print(error)
        
    def _create_table(self):
        self._cursor.execute("CREATE TABLE IF NOT EXISTS mock_exam(\
                                course CHAR(255),\
                                question LONGTEXT,\
                                options json,\
                                multi_answer BOOL,\
                                answer json\
                            )")
        self._conn.commit()

        
    def insert_data(self, course, question, options, multi_answer, answer):
        string_ = f"INSERT INTO mock_exam VALUES\
                                ('{course}', '{question}', '{json.dumps(options)}', '{multi_answer}', '{json.dumps(answer)}')"
        self._cursor.execute(string_)
        self._conn.commit()

    def read_data(self, course):
        df = pd.read_sql_query(f"SELECT * FROM mock_exam WHERE course = '{course}'", self._conn)
        return df


    def _clean_data(self):
        self._cursor.execute("DROP TABLE mock_exam")
        self._conn.commit()
