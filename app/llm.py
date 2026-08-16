import os

from dotenv import load_dotenv
from groq import Groq

from app.db import get_schema, get_foreign_keys


load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def describe_database():
    schema = get_schema()
    foreign_keys = get_foreign_keys()

    lines = []

    for table, columns in schema.items():
        lines.append(f"TABLE {table}")

        for column in columns:
            details = [column["type"]]

            if column["key"] == "PRI":
                details.append("primary key")

            if not column["nullable"]:
                details.append("not null")

            lines.append(
                f"- {column['name']}: {', '.join(details)}"
            )

        lines.append("")

    if foreign_keys:
        lines.append("RELATIONSHIPS")

        for fk in foreign_keys:
            lines.append(
                f"- {fk['TABLE_NAME']}.{fk['COLUMN_NAME']} "
                f"references "
                f"{fk['REFERENCED_TABLE_NAME']}."
                f"{fk['REFERENCED_COLUMN_NAME']}"
            )

    return "\n".join(lines)



def generate_sql(question):
    schema_description = describe_database()

    prompt = f"""
You are a SQL analytics assistant.

You are working with a MySQL database.

Database schema:

{schema_description}

User question:
{question}

Write one MySQL SELECT query that answers the user's question.

Rules:
- Only generate SELECT queries.
- Never modify the database.
- Use only tables and columns that exist in the schema.
- Use joins when necessary.
- Do not invent columns.
- Return only SQL.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
    )

    sql = response.choices[0].message.content.strip()

    sql = sql.replace("```sql", "").replace("```", "").strip()

    return sql