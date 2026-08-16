from app.db import execute_query
from app.llm import generate_sql, repair_sql, explain_results


question = input("Ask a question about the database: ")


generated = generate_sql(question)
print("\nGenerated SQL:\n")
print(generated.sql)

print("\nQuery description:\n")
print(generated.description)

try:
    results = execute_query(generated.sql)

except Exception as error:
    print("\nQuery failed.")
    print(error)

    print("\nAttempting one repair...\n")

    repaired = repair_sql(
        question,
        generated.sql,
        str(error),
    )

    print("Repaired SQL:\n")
    print(repaired.sql)

    print("\nRepair description:\n")
    print(repaired.description)

    try:
        results = execute_query(repaired.sql)
        generated = repaired

    except Exception as repair_error:
        print("\nRepair failed.")
        print(repair_error)
        raise SystemExit(1)


print("\nResults:\n")

for row in results:
    print(row)

answer = explain_results(
    question,
    generated.sql,
    results,
)

print("\nAnswer:\n")
print(answer)