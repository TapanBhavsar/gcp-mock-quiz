def check_single_answer_score(row):
    total = len(row['answer'])
    mark = 0
    if row['user_answer']:
        for user_answer in row['user_answer']:
            mark += (1 if str(int(user_answer)-1) in row['answer'] else 0) / total
    return mark
    
