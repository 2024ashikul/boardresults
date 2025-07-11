from flask import Flask, render_template_string
import sqlite3

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Student Total Marks</title>
    <style>
        table { border-collapse: collapse; width: 80%; margin: auto; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: center; cursor: pointer; }
        th { background-color: #f2f2f2; }
        th.sort-asc::after { content: " ▲"; }
        th.sort-desc::after { content: " ▼"; }
        h2 { text-align: center; }
    </style>
</head>
<body>
    <h2>Total Marks by Student</h2>
    <table id="studentsTable">
        <thead>
            <tr>
                <th>#</th>
                <th>Roll</th>
                <th>GPA</th>
                <th>Total Marks</th>
            </tr>
        </thead>
        <tbody>
            {% for idx, row in enumerate(students, start=1) %}
            <tr>
                <td>{{ idx }}</td>
                <td>{{ row['roll'] }}</td>
                <td>{{ row['gpa'] }}</td>
                <td>{{ row['total_marks'] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

<script>
// Table sorting script
document.querySelectorAll('#studentsTable th').forEach((th, index) => {
    th.addEventListener('click', () => {
        const table = th.closest('table');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isNumeric = index !== 1;  // Roll (col 1) is string, others numeric

        // Toggle sort direction
        const currentlyAsc = th.classList.contains('sort-asc');
        table.querySelectorAll('th').forEach(th => th.classList.remove('sort-asc', 'sort-desc'));
        th.classList.toggle('sort-asc', !currentlyAsc);
        th.classList.toggle('sort-desc', currentlyAsc);

        rows.sort((a, b) => {
            let aText = a.children[index].textContent.trim();
            let bText = b.children[index].textContent.trim();

            if (isNumeric) {
                aText = parseFloat(aText) || 0;
                bText = parseFloat(bText) || 0;
            }

            if (aText < bText) return currentlyAsc ? 1 : -1;
            if (aText > bText) return currentlyAsc ? -1 : 1;
            return 0;
        });

        // Re-append sorted rows and update numbering
        rows.forEach((row, i) => {
            row.children[0].textContent = i + 1;  // Update #
            tbody.appendChild(row);
        });
    });
});
</script>

</body>
</html>
'''

@app.route('/')
def show_student_totals():
    conn = sqlite3.connect('results.db')
    conn.row_factory = sqlite3.Row  # Access by column name
    cursor = conn.cursor()

    # Get column names excluding 'roll' and 'gpa'
    cursor.execute("PRAGMA table_info(students);")
    columns = [col[1] for col in cursor.fetchall() if col[1] not in ('roll', 'gpa')]

    # Get all student rows
    cursor.execute("SELECT * FROM students;")
    rows = cursor.fetchall()

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

    conn.close()

    return render_template_string(HTML_TEMPLATE, students=students, enumerate=enumerate)

if __name__ == '__main__':
    app.run(debug=True)
