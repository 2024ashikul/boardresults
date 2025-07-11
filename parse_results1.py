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

# Parse students and metadata from text
def parse_student_data(text):
    students = []
    current_group = None

    lines = text.splitlines()
    school_name = board = zilla = thana = None

    for line in lines:
        line = line.strip()
        if "BOARD OF INTERMEDIATE" in line.upper():
            board = line.strip()
        elif "INSTITUTE NAME" in line.upper():
            match = re.search(r'INSTITUTE NAME\s*:\s*(.+)', line, re.IGNORECASE)
            if match:
                school_name = match.group(1).split('(')[0].strip()
                print(f"✅ School name detected: {school_name}")
        elif line.upper().startswith("ZILLA"):
            match = re.search(r'ZILLA\s*:\s*([A-Z\s]+)', line, re.IGNORECASE)
            if match:
                zilla = match.group(1).strip()
        elif line.upper().startswith("THANA"):
            match = re.search(r'THANA\s*:\s*([A-Z\s]+)', line, re.IGNORECASE)
            if match:
                thana = match.group(1).strip()

    for line in lines:
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
                'subjects': subject_data,
                'school_name': school_name,
                'board': board,
                'zilla': zilla,
                'thana': thana
            })

    return students

def ensure_table_and_columns(conn, subject_codes):
    cursor = conn.cursor()
    # Create main table with metadata
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            roll TEXT PRIMARY KEY,
            gpa REAL,
            group_name TEXT,
            school_name TEXT,
            board TEXT,
            zilla TEXT,
            thana TEXT
        )
    """)
    # Ensure all subject code columns exist
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

    base_columns = ['roll', 'gpa', 'group_name', 'school_name', 'board', 'zilla', 'thana']
    subject_columns = [f'"{code}_marks"' for code in student['subjects']]
    all_columns = base_columns + subject_columns

    placeholders = ','.join('?' * len(all_columns))
    values = [
        student['roll'],
        student['gpa'],
        student['group'],
        student.get('school_name', ''),
        student.get('board', ''),
        student.get('zilla', ''),
        student.get('thana', '')
    ] + list(student['subjects'].values())

    sql = f"""
        INSERT OR REPLACE INTO students ({','.join(all_columns)}) 
        VALUES ({placeholders})
    """
    cursor.execute(sql, values)
    conn.commit()

def process_pdfs():
    conn = sqlite3.connect(DB_FILE)
    for file in os.listdir(PDF_FOLDER):
        if file.endswith('.pdf'):
            print(f"📄 Processing {file}...")
            pdf_path = os.path.join(PDF_FOLDER, file)
            text = extract_text(pdf_path)
            students = parse_student_data(text)
            if not students:
                print(f"⚠️  No students found in {file}")
                continue
            all_subjects = set(code for s in students for code in s['subjects'])
            ensure_table_and_columns(conn, all_subjects)
            for s in students:
                insert_student_data(conn, s)
    conn.close()
    print("✅ All PDFs processed.")

if __name__ == "__main__":
    os.makedirs(PDF_FOLDER, exist_ok=True)
    process_pdfs()
