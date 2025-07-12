from flask import Flask, render_template, request
import sqlite3
import math
import os

app = Flask(__name__)


subject_id_name_map = {
    '101': 'Bangla',
    '107': 'English',
    '108': 'English 2nd Paper',
    '154': 'Information & Communication Technology',
    '126' : 'Higer Mathematics',
    '152': 'Finance and Banking',
    '143': 'Business Entrepreneurship',
    '147': 'Physical Education, Health, and Sports',
    '153': 'History of Bangladesh and World Civilization',
    '134': 'Agriculture Studies ',
    '111': 'Islam and Moral Education',
    '112': 'Hindu and Moral Education',
    '127': 'Science',
    '150': 'Bangladesh and Global Studies',
    '156': 'Career Education',
    '110': 'Geography and Environment (Old)',
    '109': 'Mathematics',
    '136' : 'Physics',
    '138' : 'Biology',
    '137' : 'Chemistry',
    '146' : 'Accounting',
    '151' :'Home Science',
    '153' :'HISTORY OF BANGLADESH AND WORLD CIVILIZATION',
    '140' : 'CIVICS AND CITIZENSHIP',
    '110' :'GEOGRAPHY AND ENVIRONMENT'
}


@app.route('/')
def show_student_totals():
    search_roll = request.args.get('roll', '').strip()
    selected_group = request.args.get('group', 'all')
    page = int(request.args.get('page', 1))
    per_page = 100

    conn = sqlite3.connect('results.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get subject columns
    cursor.execute("PRAGMA table_info(students);")
    all_cols = [col[1] for col in cursor.fetchall()]
    exclude_cols = ('roll', 'gpa', 'group_name', 'school_name', 'board', 'zilla', 'thana')
    marks_cols = [c for c in all_cols if c not in exclude_cols]

    # Get all student rows
    cursor.execute("SELECT * FROM student")
    rows = cursor.fetchall()

    students = []
    for row in rows:
        subject_marks = {
        col: row[col] for col in marks_cols if row[col] not in (None, 0)
        }
        total = sum(float(row[col] or 0) for col in marks_cols)

        students.append({
            
            'roll': row['roll_no'],
            'name' : row['name'],
            'gpa': row['gpa'],
            'group': row['group'],
            'school_name': row['institute'],
            'total_marks': row['sum'],
            'subject_marks': subject_marks
        })

    # Group filter
    if selected_group.lower() != 'all':
        filtered_students = [s for s in students if s['group'].lower() == selected_group.lower()]
    else:
        filtered_students = students

    filtered_students.sort(key=lambda x: x['total_marks'], reverse=True)

    # Assign rank
    for idx, s in enumerate(filtered_students, start=1):
        s['rank'] = idx

    # Roll filter (disable pagination)
    if search_roll:
        filtered_students = [s for s in filtered_students if str(s['roll']) == search_roll]
        total_pages = 1
        page_students = filtered_students
    else:
        total_students = len(filtered_students)
        total_pages = math.ceil(total_students / per_page)
        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        end = start + per_page
        page_students = filtered_students[start:end]

    conn.close()

    return render_template(
        'students.html',
        students=page_students,
        search_roll=search_roll,
        selected_group=selected_group,
        page=page,
        total_pages=total_pages
    )

@app.route('/result/<int:roll>')
def student_result(roll):
    conn = sqlite3.connect('results.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM student WHERE roll_no = ?", (roll,))
    row = cursor.fetchone()

    if row is None:
        return "Student not found", 404
    
    

    student = dict(row)  # ✅ Convert entire row to dictionary
    items = list(student.items())
    sum_index = next(i for i, (k, v) in enumerate(items) if k == 'sum')
    print(student)
    subjects = {k: v for k, v in items[sum_index+1:] if v is not None}
    subjects.pop('createdAt', None)  # Remove createdAt if exists
    subjects.pop('updatedAt', None)
    return render_template('student_result.html', student=student, subjects= subjects)

@app.route('/ins/<string:school>')
def institute_result(school):
    search_roll = request.args.get('roll', '').strip()
    selected_group = request.args.get('group', 'all')
    page = int(request.args.get('page', 1))
    per_page = 100

    conn = sqlite3.connect('results.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get subject columns
    cursor.execute("PRAGMA table_info(students);")
    all_cols = [col[1] for col in cursor.fetchall()]
    exclude_cols = ('roll', 'gpa', 'group_name', 'school_name', 'board', 'zilla', 'thana')
    marks_cols = [c for c in all_cols if c not in exclude_cols]

    # Get all student rows
    cursor.execute("SELECT * FROM student where institute = ? " ,(school ,))
    rows = cursor.fetchall()

    students = []
    for row in rows:
        subject_marks = {
        col: row[col] for col in marks_cols if row[col] not in (None, 0)
        }
        total = sum(float(row[col] or 0) for col in marks_cols)

        students.append({
            
            'roll': row['roll_no'],
            'name' : row['name'],
            'gpa': row['gpa'],
            'group': row['group'],
            'school_name': row['institute'],
            'total_marks': row['sum'],
            'subject_marks': subject_marks
        })

    # Group filter
    if selected_group.lower() != 'all':
        filtered_students = [s for s in students if s['group'].lower() == selected_group.lower()]
    else:
        filtered_students = students

    filtered_students.sort(key=lambda x: x['total_marks'], reverse=True)

    # Assign rank
    for idx, s in enumerate(filtered_students, start=1):
        s['rank'] = idx

    # Roll filter (disable pagination)
    if search_roll:
        filtered_students = [s for s in filtered_students if str(s['roll']) == search_roll]
        total_pages = 1
        page_students = filtered_students
    else:
        total_students = len(filtered_students)
        total_pages = math.ceil(total_students / per_page)
        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        end = start + per_page
        page_students = filtered_students[start:end]

    conn.close()

    return render_template(
        'students.html',
        students=page_students,
        search_roll=search_roll,
        selected_group=selected_group,
        page=page,
        total_pages=total_pages
    )

@app.route('/about')
def about():
    return render_template('about.htm')

if __name__ == "__main__":
    app.run()
