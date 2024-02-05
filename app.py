from flask import Flask, request, render_template, redirect, session, jsonify
from flask_session import Session
from datetime import datetime, timedelta

import pandas as pd

from src import engine
from src import config


app = Flask(__name__)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

engine_obj = engine.Engine(clean_start=False)

@app.route('/', methods=['GET']) 
def home(): 
    return render_template("home.html")

@app.route('/pmle_exam', methods=['GET'])
def pmle_exam():
    question_df = engine_obj.get_course_questions("PMLE")
    session['question_df'] = question_df.to_dict()
    session['exam_start'] = False
    return render_template('exam_form.html',
                           timing = config.EXAM_TIMING_IN_HOURS,
                           number_of_questions = len(question_df))

@app.route('/question/<id>', methods=['GET'])
def question(id):
    if not session.get('exam_start'):
        session['end_time'] = datetime.now() + timedelta(hours=config.EXAM_TIMING_IN_HOURS)
        session['exam_start'] = True
    question_dict = session.get("question_df", None)
    question_df = pd.DataFrame(question_dict)
    return render_template('question.html',
                           question=question_df.loc[int(id),'question'],
                           question_index=int(id),
                           options=question_df.loc[int(id), 'options'],
                           multi_answer=question_df.loc[int(id), 'multi_answer'],
                           user_answers=question_df.loc[int(id), 'user_answer'],
                           next_button=True if int(id) < len(question_df)-1 else False,
                           previous_button=True if int(id) > 0 else False,
                           preview=question_df.loc[int(id), 'preview'])

def get_question_df_with_reform():
    question_dict = session.get("question_df", None)
    question_df = pd.DataFrame(question_dict)
    
    user_answer = request.form.getlist('user_answers[]')
    question_index = request.form.get('question_index', None)
    if question_index:
        question_index = int(question_index)
        preview = bool(request.form.get('preview', None))

        if question_df.loc[int(question_index), 'user_answer'] != user_answer:
            question_df.loc[int(question_index), 'user_answer'] = user_answer
        question_df.loc[int(question_index), 'preview'] = preview
    session['question_df'] = question_df.to_dict()

    return question_index, question_df
        
@app.route('/next', methods=['POST'])
def next_question():
    question_index, question_df = get_question_df_with_reform()
    if question_index < len(question_df) - 1:
        question_index += 1
    return render_template('question.html', 
                           question=question_df.loc[int(question_index), 'question'],
                           question_index=question_index,
                           options=question_df.loc[int(question_index), 'options'],
                           multi_answer=question_df.loc[int(question_index), 'multi_answer'],
                           user_answers=question_df.loc[int(question_index), 'user_answer'],
                           next_button=True if question_index < len(question_df)-1 else False,
                           previous_button=True,
                           preview=question_df.loc[int(question_index), 'preview'])

@app.route('/previous', methods=['POST'])
def previous_question():
    question_index, question_df = get_question_df_with_reform()

    if question_index > 0:
        question_index -= 1
    return render_template('question.html',
                           question=question_df.loc[int(question_index), 'question'],
                           question_index=question_index,
                           options=question_df.loc[int(question_index), 'options'],
                           multi_answer=question_df.loc[int(question_index), 'multi_answer'],
                           user_answers=question_df.loc[int(question_index), 'user_answer'],
                           next_button=True,
                           previous_button=True if question_index > 0 else False,
                           preview=question_df.loc[int(question_index), 'preview'])

@app.route('/preview', methods=['POST'])
def preview():
    _, question_df = get_question_df_with_reform()
    question_df = question_df.reset_index(names=['index'])
    return render_template('preview.html',
                           preview_with_id=question_df[['index','preview']].values.tolist())

@app.route('/assessment', methods=['POST'])
def assessment():
    _, question_df = get_question_df_with_reform()
    result="pass" if engine_obj.is_passed(question_df) else "failed"
    return f"you have {result} the exam"

@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    return render_template('add_question_form.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        course = request.form.get('course')
        question = request.form.get('question')
        has_multiple_answer = request.form.get('m_answer')
        options = request.form.getlist('options[]')
        answers = request.form.getlist('answers[]')

        engine_obj.add_question(course=course,
                                question=question,
                                options=options,
                                answer=answers,
                                is_multi_answer= True if has_multiple_answer else False)
        
    return redirect('/add_question')

@app.route('/remaining-time')
def remaining_time():
    end_time = session.get('end_time')
    now = datetime.now()
    time_diff = end_time.replace(tzinfo=None) - now
    hours = time_diff.seconds // 3600
    minutes = (time_diff.seconds // 60) % 60
    seconds = time_diff.seconds % 60
    return jsonify({'hours': hours, 'minutes': minutes, 'seconds': seconds})


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run(debug=True)