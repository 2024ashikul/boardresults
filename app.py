from flask import Flask, render_template, request
import sqlite3
import math

app = Flask(__name__)

@app.route('/')
def show_student_totals():
    search_roll = request.args.get('roll', '').strip()
    selected_group = request.args.get('group', 'all')
    page = int(request.args.get('page', 1))
    per_page = 100  

    conn = sqlite3.connect('results.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all subject columns except metadata
    cursor.execute("PRAGMA table_info(students);")
    all_cols = [col[1] for col in cursor.fetchall()]
    marks_cols = [c for c in all_cols if c not in (
        'roll', 'gpa', 'group_name', 'school_name', 'board', 'zilla', 'thana'
    )]

    # Fetch all GPA=5 students
    cursor.execute("SELECT * FROM students WHERE gpa = 5.0")
    rows = cursor.fetchall()

    # Build students list with total marks
    students = []
    for row in rows:
        total = sum(float(row[col] or 0) for col in marks_cols)
        students.append({
            'roll': row['roll'],
            'gpa': row['gpa'],
            'group': row['group_name'],
            'school_name': row['school_name'],
            'total_marks': round(total + 150, 2)  # +150 boost
        })

    # Filter by group if not "all"
    if selected_group.lower() != 'all':
        filtered_students = [s for s in students if s['group'].lower() == selected_group.lower()]
    else:
        filtered_students = students

    # Sort by total marks (descending)
    filtered_students.sort(key=lambda x: x['total_marks'], reverse=True)

    # Assign ranks
    for idx, s in enumerate(filtered_students, start=1):
        s['rank'] = idx

    # Search by roll (bypass pagination)
    if search_roll:
        filtered_students = [s for s in filtered_students if str(s['roll']) == search_roll]
        total_students = len(filtered_students)
        total_pages = 1
        page_students = filtered_students
    else:
        total_students = len(filtered_students)
        total_pages = math.ceil(total_students / per_page)
        # Clamp page number
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

if __name__ == '__main__':
    app.run(debug=True)
