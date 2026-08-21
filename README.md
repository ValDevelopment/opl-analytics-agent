# OpenPowerlifting Analytics Agent

An LLM-powered natural-language query agent for the OpenPowerlifting relational MySQL database. The agent translates plain-English questions into MySQL queries, validates and executes them safely, automatically repairs queries that fail, and returns a grounded natural-language answer alongside the underlying SQL and results.

## Objective

The objective of this project is to provide a conversational interface over the relational database built in the opl-relational-db project, allowing questions about lifters, meets, and competition results to be answered without writing SQL directly.

The project focuses on three connected tasks:

1. Generating valid, read-only MySQL queries from natural-language questions.
2. Enforcing query safety independently of the language model's own judgment.
3. Producing a natural-language answer that is grounded in the actual query results.

## Data Source

This project does not process or load new data. It connects to and queries the existing relational database built in the opl-relational-db project, which contains the lifters, meets, and results tables. That database must be created and populated before this agent can be used.

## Architecture

The agent is organized into three modules under `app/`:

- `db.py`: manages the MySQL connection, introspects the database schema and foreign-key relationships from `INFORMATION_SCHEMA`, validates generated SQL, and executes queries.
- `llm.py`: builds prompts for the Groq API and defines the three language-model calls used by the agent, namely SQL generation, SQL repair, and result explanation.
- `agent.py`: orchestrates the end-to-end flow and returns a single typed response object.

`main.py` provides a command-line entry point that accepts a question, runs it through the agent, and prints the generated SQL, description, results, and final answer.

## Methodology

### Part 1: Schema Introspection

Before generating a query, the agent builds a text description of the database by querying `INFORMATION_SCHEMA.COLUMNS` and `INFORMATION_SCHEMA.KEY_COLUMN_USAGE`. This description includes table names, column names, types, nullability, primary keys, and foreign-key relationships. Because the schema is retrieved dynamically at request time rather than hardcoded, the agent adapts automatically if the underlying database changes.

### Part 2: SQL Generation

The schema description and the user's question are sent to a Groq-hosted language model with a structured prompt. The model is instructed to return a single read-only MySQL query along with a short description, and the response is parsed into a Pydantic model (`SQLGeneration`) rather than treated as free text. The prompt also instructs the model to distinguish between questions asking for unique entities (such as top lifters or federations) and questions asking for individual records, to avoid duplicate entities in aggregate-style answers.

### Part 3: Query Validation

Generated SQL is parsed with SQLGlot before execution. Validation rejects the query if it does not parse as valid MySQL, if it contains more than one statement, if it is not a query expression (SELECT), or if it contains a write or DDL operation such as `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, or `ALTER` anywhere in the parsed statement tree. This check operates on the parsed SQL structure rather than the prompt instructions alone, so it functions as a validation layer independent of the language model's own behavior.

### Part 4: Query Execution

Validated queries are executed against the MySQL database with `mysql-connector-python`, and results are returned as a list of dictionaries.

### Part 5: Automatic Repair

If query execution raises an error, the original question, the failed SQL, and the database error message are sent back to the language model in a separate repair prompt. The repair prompt carries additional rules distinguishing `DISTINCT` from aggregation, since the results table stores one row per competition entry, and ranking unique lifters or federations by a metric such as total requires grouping and aggregation rather than a plain `DISTINCT`. If the repaired query succeeds, the response is flagged as repaired. If it fails again, the agent returns the error rather than retrying further.

### Part 6: Result Explanation

Once a query succeeds, the question, the executed SQL, and the returned rows are sent to the language model with instructions to answer using only the returned data, without introducing facts not present in the results.

## Example Interaction

```
Ask a question about the database: Which federation has the most results in the dataset?

Generated SQL:
SELECT Federation, COUNT(*) AS ResultCount
FROM meets
JOIN results ON meets.MeetID = results.MeetID
GROUP BY Federation
ORDER BY ResultCount DESC
LIMIT 1;

Query description:
Counts results per federation and returns the federation with the highest count.

Results:
{'Federation': '...', 'ResultCount': ...}

Answer:
...
```

## Design Notes

- Read-only enforcement is implemented by inspecting the parsed SQL statement tree rather than relying solely on prompt instructions, so a query is blocked even if the model does not follow the stated rules.
- The repair step runs once per question rather than in an open-ended retry loop, so a query that cannot be corrected surfaces a clear error instead of looping silently.
- Row limits are currently enforced only through prompt instructions to the model, not through the database driver or a hard query-level cap.
- Structured outputs (Pydantic models) are used for both the SQL-generation and repair steps so that responses are parsed and validated rather than treated as free text.
- `test_db.py` exercises the statement-count guard directly by submitting a two-statement string containing a `SELECT` followed by a `DELETE`, confirming that the validator rejects it before execution.

## Repository Structure

```
opl-analytics-agent/
├── app/
│   ├── __init__.py
│   ├── agent.py        # orchestration: generate, execute, repair, explain
│   ├── db.py            # connection, schema introspection, validation, execution
│   └── llm.py            # Groq prompts for generation, repair, and explanation
├── main.py                # command-line entry point
├── test_db.py               # validation test for multi-statement/write rejection
├── requirements.txt
└── .gitignore
```

## Usage

1. Set up and populate the relational database from the opl-relational-db project.
2. Clone this repository.
3. Install dependencies:

```
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following variables:

```
GROQ_API_KEY=
GROQ_MODEL=
DB_HOST=
DB_PORT=
DB_USER=
DB_PASSWORD=
DB_NAME=
```

5. Run the agent:

```
python main.py
```

6. Enter a natural-language question about lifters, meets, or results when prompted.

## Limitations

- The agent runs as a command-line tool only; there is no web or API interface at this stage.
- Row limits depend on the language model following prompt instructions rather than a database-level cap.
- The automatic repair step makes a single correction attempt; further failures are returned as errors.
- Query validation blocks statement types and write operations, but does not restrict access to specific tables or columns, or guard against computationally expensive read queries.
- The agent has no conversation memory; each question is answered independently of prior questions.
- Behavior depends on the Groq API and the configured model, so results may vary if the model is changed or deprecated.

## Potential Extensions

Future development may include:

- adding a web interface for the agent
- adding multi-turn conversational context
- caching the schema description instead of querying `INFORMATION_SCHEMA` on every request
- adding a hard row-limit enforced at the database or driver level
- restricting access to specific tables or columns
- logging generated queries and repairs for auditing
- expanding automated test coverage for additional validation edge cases

## References

- OpenPowerlifting relational database (opl-relational-db)
- Groq API documentation
- SQLGlot documentation
- Pydantic documentation
