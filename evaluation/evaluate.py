import csv

from app.agent import answer_question


passed = 0
total = 0


with open("evaluation/questions.csv", newline="", encoding="utf-8") as file:
    questions = csv.DictReader(file)

    for item in questions:
        response = answer_question(item["question"])

        total += 1

        print(f"\nQuestion {item['id']}:")
        print(item["question"])

        if response.error:
            print("FAILED - execution error")
            continue

        expected = item["expected_value"]

        result_text = str(response.results)

        if expected and expected in result_text:
            passed += 1
            print("PASS")
        else:
            print("FAIL")

        print("SQL:")
        print(response.sql)

        print("Results:")
        print(response.results)


print(f"\nScore: {passed}/{total}")