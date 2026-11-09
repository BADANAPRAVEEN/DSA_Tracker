const API = "http://127.0.0.1:8000";
const list = document.getElementById("list");

async function loadProblems() {
    const res = await fetch(API + "/problems");
    if (!res.ok) { list.textContent = "Error: " + res.status; return; }
    const problems = await res.json();

    list.innerHTML = "";
    problems.forEach(p => {
        const li = document.createElement("li");
        li.textContent = p.title + " (" + p.topic + ") ";
        const btn = document.createElement("button");
        btn.textContent = "Delete";
        btn.addEventListener("click", () => deleteProblem(p.id));
        li.appendChild(btn);
        list.appendChild(li);
    });
}

async function addProblem() {
    const title = document.getElementById("title").value;
    const topic = document.getElementById("topic").value;
    const res = await fetch(API + "/problems", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title, topic: topic }),
    });
    if (!res.ok) { alert("Failed: " + res.status); return; }
    loadProblems();
}

async function deleteProblem(id) {
    const res = await fetch(API + "/problems/" + id, { method: "DELETE" });
    if (!res.ok) { alert("Failed: " + res.status); return; }
    loadProblems();
}

document.getElementById("add").addEventListener("click", addProblem);
loadProblems();