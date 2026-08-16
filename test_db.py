from app.db import execute_query

execute_query("""
SELECT * FROM lifters LIMIT 5;
DELETE FROM lifters;
""")