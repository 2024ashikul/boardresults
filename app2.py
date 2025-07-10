from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

@app.route('/')
def show_student_totals():
    search_roll = request.args.get('roll', '').strip()
    
    conn = sqlite3.connect('results.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(students);")
    columns = [col[1] for col in cursor.fetchall() if col[1] not in ('roll', 'gpa')]

    # Get all students
    cursor.execute("SELECT * FROM students;")
    rows = cursor.fetchall()
    conn.close()

    students = []
    for row in rows:
        total = 0
        for col in columns:
            try:
                val = float(row[col]) if row[col] else 0
                total += val
            except ValueError:
                pass
        students.append({
            'roll': row['roll'],
            'gpa': row['gpa'],
            'total_marks': round(total, 2) + 150
        })

    # Sort all students by total_marks descending
    students.sort(key=lambda x: x['total_marks'], reverse=True)

    # Add rank/index
    for idx, student in enumerate(students, start=1):
        student['rank'] = idx

    # If searching for one student, filter
    if search_roll:
        students = [s for s in students if s['roll'] == search_roll]

    return render_template("students.html", students=students,enumerate = enumerate,search_roll=search_roll)
if __name__ == '__main__':
    app.run(debug=True)
