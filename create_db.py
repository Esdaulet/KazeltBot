import sqlite3

# Создаем или подключаемся к базе данных
conn = sqlite3.connect('members.db')
cursor = conn.cursor()

# Создаем таблицу, если она не существует
cursor.execute('''
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    full_name TEXT,
    work_place TEXT,
    age INTEGER,
    teaching_experience TEXT,
    city TEXT,
    receipt_file_path TEXT,
    registration_date TEXT
)
''')

# Сохраняем изменения и закрываем соединение
conn.commit()
conn.close()
