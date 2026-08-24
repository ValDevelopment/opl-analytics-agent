import os

from dotenv import load_dotenv
from groq import Groq

from app.db import get_schema, get_foreign_keys

from pydantic import BaseModel

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL")

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

            line = f"- {column['name']}: {', '.join(details)}"

            if table == "lifters" and column["name"] == "Sex":
                line += " | observed values: F, M"

            if table == "results" and column["name"] == "WeightClassKg":
                line += " | examples: 83, 93, 105, 120, 120+"

            lines.append(line)

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

Return a JSON object with exactly these fields:

{{
  "sql": "one MySQL query",
  "description": "short description of what the query does"
}}

Rules:
- Only generate read-only queries.
- Use only tables and columns that exist in the schema.
- Use joins when necessary.
- Do not invent columns.
- Pay attention to whether the user is asking for unique entities versus individual records.
- If asking for top lifters, teams, federations, etc., avoid duplicate entities unless the question explicitly asks for individual performances or records.
- Unless the user explicitly requests more rows, limit result sets to at most 100 rows.
- Return valid JSON only.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    result = SQLGeneration.model_validate_json(
        response.choices[0].message.content
    )

    return result


def explain_results(question, sql, results):
    prompt = f"""
You are a data analyst.

The user asked:
{question}

The following SQL query was executed:

{sql}

The database returned:

{results}

Answer the user's question using only the returned data.

Rules:
- Do not invent facts that are not present in the results.
- Do not claim anything beyond what the query results support.
- Be concise and direct.
- Include relevant numbers.
- Do not discuss the SQL unless it is necessary to explain the answer.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
    )

    return response.choices[0].message.content.strip()



class SQLGeneration(BaseModel):
    sql: str
    description: str




def repair_sql(question, sql, error):
    schema_description = describe_database()

    prompt = f"""
You are fixing a failed MySQL query.

Database schema:

{schema_description}

Original user question:
{question}

Failed SQL:
{sql}

Database error:
{error}

Return a JSON object with exactly these fields:

{{
  "sql": "corrected MySQL query",
  "description": "short description of what was fixed"
}}

Rules:
- Fix the query so it answers the original question.
- Only generate read-only queries.
- Use only tables and columns that exist in the schema.
- Do not invent columns or tables.
- Preserve the user's original analytical intent.
- Return valid JSON only.
- Preserve the original user's semantics, not just SQL validity.
- If the original question asks for unique entities such as lifters, teams, or federations, do not return duplicate entities unless explicitly requested.
- Preserve the original analytical meaning of the user's question, not just SQL validity.
- When ranking unique entities by a numeric metric across multiple records, aggregate the metric per entity before ranking.
- For questions such as "lifters with the highest total", use an aggregation such as MAX(...) with GROUP BY rather than DISTINCT.
- Do not use DISTINCT as a substitute for grouping when the user is asking for the best, highest, lowest, average, or total metric per entity.
- Ensure ORDER BY expressions are valid for the generated SELECT statement.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    return SQLGeneration.model_validate_json(
        response.choices[0].message.content
    )