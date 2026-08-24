const form = document.getElementById("question-form");
const questionInput = document.getElementById("question");
const status = document.getElementById("status");
const responseSection = document.getElementById("response");

const answerElement = document.getElementById("answer");
const sqlElement = document.getElementById("sql");
const descriptionElement = document.getElementById("description");
const resultsElement = document.getElementById("results");


form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = questionInput.value.trim();

    if (!question) {
        return;
    }

    status.textContent = "Analyzing...";
    responseSection.classList.add("hidden");

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                question: question,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error("Request failed.");
        }

        if (data.error) {
            throw new Error(data.error);
        }

        answerElement.textContent = data.answer;
        sqlElement.textContent = data.sql;
        descriptionElement.textContent = data.description;

        renderResults(data.results);

        status.textContent = data.was_repaired
            ? "Completed after automatically repairing the SQL query."
            : "";

        responseSection.classList.remove("hidden");

    } catch (error) {
        status.textContent = `Error: ${error.message}`;
    }
});


function renderResults(results) {
    resultsElement.innerHTML = "";

    if (!results || results.length === 0) {
        resultsElement.textContent = "No results.";
        return;
    }

    const table = document.createElement("table");

    const columns = Object.keys(results[0]);

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    columns.forEach((column) => {
        const th = document.createElement("th");
        th.textContent = column;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");

    results.forEach((row) => {
        const tr = document.createElement("tr");

        columns.forEach((column) => {
            const td = document.createElement("td");
            td.textContent = row[column] ?? "";
            tr.appendChild(td);
        });

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    resultsElement.appendChild(table);
}