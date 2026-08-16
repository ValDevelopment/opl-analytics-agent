from app.llm import generate_sql


question = input("Ask a question about the database: ")

sql = generate_sql(question)

print("\nGenerated SQL:\n")
print(sql)