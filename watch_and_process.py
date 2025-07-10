import os
import re
import sqlite3
from pdfminer.high_level import extract_text

PDF_FOLDER = 'pdfs'
DB_FILE = 'results.db'

# Extract roll, GPA, and subjects with marks
def parse_student_data(text):
    students = []
    for match in re.finditer(r"(\d{6})\[(\d\.\d{2})]:([^\n]+)", text):
        roll, gpa, subjects_raw = match.groups()
        subject_data = {}
        for part in subjects_raw.split(','):
            part = part.strip()
            subject_match = re.match(r"(\d+):T:(\d+)", part)
            if subject_match:
                code, marks = subject_match.groups()
                subject_data[code] = marks
        students.append({
            'roll': roll,
            'gpa': float(gpa),
            'subjects': subject_data
        })
    return students

# Ensure table and dynamic columns
def ensure_table_and_columns(conn, subject_codes):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            roll TEXT PRIMARY KEY,
            gpa REAL
        )
    """)
    for code in subject_codes:
        col = f'"{code}_marks"'
        cursor.execute(f"""
            ALTER TABLE students ADD COLUMN {col} TEXT
        """) if not column_exists(conn, col) else None
    conn.commit()

def column_exists(conn, col):
    cursor = conn.execute("PRAGMA table_info(students)")
    return any(col.strip('"') == row[1] for row in cursor.fetchall())

# Insert or update data
def insert_student_data(conn, student):
    cursor = conn.cursor()
    columns = ['roll', 'gpa'] + [f'"{code}_marks"' for code in student['subjects']]
    placeholders = ','.join('?' * len(columns))
    values = [student['roll'], student['gpa']] + list(student['subjects'].values())
    sql = f"""
        INSERT OR REPLACE INTO students ({','.join(columns)}) 
        VALUES ({placeholders})
    """
    cursor.execute(sql, values)
    conn.commit()

# Process all PDFs
def process_pdfs():
    conn = sqlite3.connect(DB_FILE)
    for file in os.listdir(PDF_FOLDER):
        if file.endswith('.pdf'):
            pdf_path = os.path.join(PDF_FOLDER, file)
            print(f"Processing {file}...")
            text = extract_text(pdf_path)
            students = parse_student_data(text)
            all_subjects = set(code for s in students for code in s['subjects'])
            ensure_table_and_columns(conn, all_subjects)
            for s in students:
                insert_student_data(conn, s)
    conn.close()
    print("✅ All PDFs processed.")

if __name__ == "__main__":
    os.makedirs(PDF_FOLDER, exist_ok=True)
    process_pdfs()
