import os
import re
import sqlite3
from pdfminer.high_level import extract_text

PDF_FOLDER = 'pdfs'
DB_FILE = 'results.db'

# Detect group from a roll number block
def detect_group(line):
    if "SCIENCE" in line:
        return "Science"
    elif "BUSINESS STUDIES" in line:
        return "Business Studies"
    elif "HUMANITIES" in line:
        return "Humanities"
    return None

def parse_student_data(text):
    students = []
    current_group = None
    for line in text.splitlines():
        line = line.strip()
        detected = detect_group(line.upper())
        if detected:
            current_group = detected
            continue

        match = re.match(r"(\d{6})\[(\d\.\d{2})]:([^\n]+)", line)
        if match:
            roll, gpa, subjects_raw = match.groups()
            subject_data = {}
            for part in subjects_raw.split(','):
                part = part.strip()
                sub_match = re.match(r"(\d+):T:(\d+)", part)
                if sub_match:
                    code, marks = sub_match.groups()
                    subject_data[code] = marks
            students.append({
                'roll': roll,
                'gpa': float(gpa),
                'group': current_group,
                'subjects': subject_data
            })
    return students

def ensure_table_and_columns(conn, subject_codes):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            roll TEXT PRIMARY KEY,
            gpa REAL,
            group_name TEXT
        )
    """)
    for code in subject_codes:
        col = f'"{code}_marks"'
        if not column_exists(conn, col):
            cursor.execute(f'ALTER TABLE students ADD COLUMN {col} TEXT')
    conn.commit()

def column_exists(conn, col):
    cursor = conn.execute("PRAGMA table_info(students)")
    return any(col.strip('"') == row[1] for row in cursor.fetchall())

def insert_student_data(conn, student):
    cursor = conn.cursor()
    columns = ['roll', 'gpa', 'group_name'] + [f'"{code}_marks"' for code in student['subjects']]
    placeholders = ','.join('?' * len(columns))
    values = [student['roll'], student['gpa'], student['group']] + list(student['subjects'].values())
    sql = f"""
        INSERT OR REPLACE INTO students ({','.join(columns)}) 
        VALUES ({placeholders})
    """
    cursor.execute(sql, values)
    conn.commit()

def process_pdfs():
    conn = sqlite3.connect(DB_FILE)
    for file in os.listdir(PDF_FOLDER):
        if file.endswith('.pdf'):
            print(f"Processing {file}...")
            pdf_path = os.path.join(PDF_FOLDER, file)
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
