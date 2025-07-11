from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

@app.route('/')
def show_student_totals():
    search_roll = request.args.get('roll', '').strip()
    selected_group = request.args.get('group', 'all')

    conn = sqlite3.connect('results.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get subject columns (excluding non-marks fields)
    cursor.execute("PRAGMA table_info(students);")
    columns = [col[1] for col in cursor.fetchall() if col[1] not in (
        'roll', 'gpa', 'group_name', 'school_name', 'board', 'zilla', 'thana')]

    # Step 1: Fetch all GPA 5 students
    cursor.execute("SELECT * FROM students WHERE gpa = 5.0")
    all_rows = cursor.fetchall()

    all_students = []
    for row in all_rows:
        total = sum(float(row[col] or 0) for col in columns)
        all_students.append({
            'roll': row['roll'],
            'gpa': row['gpa'],
            'group': row['group_name'],
            'school_name': row['school_name'],
            'total_marks': round(total, 2) + 150  # Apply +150
        })

    # Step 2: Rank all students globally
    all_students.sort(key=lambda x: x['total_marks'], reverse=True)
    roll_to_rank = {}
    for idx, student in enumerate(all_students, start=1):
        student['rank'] = idx
        roll_to_rank[student['roll']] = student

    # Step 3: Apply filters for final display
    filtered_students = []
    for student in all_students:
        if selected_group.lower() != 'all' and student['group'] != selected_group:
            continue
        if search_roll and str(student['roll']) != search_roll:
            continue
        filtered_students.append(student)

    return render_template(
        "students.html",
        students=filtered_students,
        search_roll=search_roll,
        selected_group=selected_group
    )

@app.route('/about')
def about():
    return render_template('about.htm')

if __name__ == '__main__':
    app.run(debug=True)
