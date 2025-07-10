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

    cursor.execute("PRAGMA table_info(students);")
    columns = [col[1] for col in cursor.fetchall() if col[1] not in ('roll', 'gpa', 'group_name')]

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
            'group': row['group_name'],
            'total_marks': round(total, 2) + 150
        })

    # Filter by group if selected and not 'all'
    if selected_group.lower() != 'all':
        students = [s for s in students if s['group'] == selected_group]

    # If searching by roll, filter first (so search works even with group filter)
    if search_roll:
        students = [s for s in students if s['roll'] == search_roll]

    # Sort and re-rank students after filtering
    students.sort(key=lambda x: x['total_marks'], reverse=True)
    for idx, student in enumerate(students, start=1):
        student['rank'] = idx

    return render_template(
        "students.html",
        students=students,
        search_roll=search_roll,
        selected_group=selected_group
    )

@app.route('/about')
def about():
    return "<h1>About This App</h1><p>This app displays student marks by group and roll number.</p>"


if __name__ == '__main__':
    app.run(debug=True)
