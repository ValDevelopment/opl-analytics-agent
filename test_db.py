from app.db import get_connection


connection = get_connection()
cursor = connection.cursor()

cursor.execute("SHOW TABLES;")

for table in cursor.fetchall():
    print(table[0])

cursor.close()
connection.close()