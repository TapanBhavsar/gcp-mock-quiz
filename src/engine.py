import json
import numpy as np

from src import config
from src.sql import SqlConnection
from src.assessment import *


class Engine:
    def __init__(self, clean_start=False):
        self.sql_connector = SqlConnection(config.DATABASE, clean_start)
    
    def __del__(self):
        del self.sql_connector

    def add_question(self, course, question, options, answer, is_multi_answer):
        self.sql_connector.insert_data(course=course, 
                                       question=question,
                                       options=options,
                                       answer=answer,
                                       multi_answer=is_multi_answer)
        
    def get_course_questions(self, course):
        df = self.sql_connector.read_data(course)
        df['options'] = df['options'].apply(json.loads)
        df['answer'] = df['answer'].apply(json.loads)
        df['user_answer'] = None
        df['preview'] = None
        if len(df) > config.NUMBER_OF_QUESTIONS:
            df=df.sample(n=config.NUMBER_OF_QUESTIONS)
        return df

    @staticmethod
    def is_passed(submission_df):
        submission_df['mark'] = submission_df.apply(check_single_answer_score, axis=1)
        return True if ((submission_df['mark'].sum()/len(submission_df)) 
                        >= config.PASSING_THRESHOLD) else False
