from app.agent import answer_question


question = input("Ask a question about the database: ")

response = answer_question(question)

if response.error:
    print("\nQuery failed:\n")
    print(response.error)

else:
    print("\nGenerated SQL:\n")
    print(response.sql)

    print("\nQuery description:\n")
    print(response.description)

    if response.was_repaired:
        print("\nNote: the original query was automatically repaired.")

    print("\nResults:\n")

    for row in response.results:
        print(row)

    print("\nAnswer:\n")
    print(response.answer)