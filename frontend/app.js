const API =
    location.hostname === "127.0.0.1" || location.hostname === "localhost"
        ? "http://127.0.0.1:8000"
        : "https://dsa-tracker-wakr.onrender.com";

const list = document.getElementById("list");

async function loadProblems() {
    const res = await fetch(API + "/problems");
    if (!res.ok) { list.textContent = "Error: " + res.status; return; }
    const problems = await res.json();

    list.innerHTML = "";
    problems.forEach(p => {
        const li = document.createElement("li");
        li.textContent = (p.solved ? "✅ " : "❌ ") + p.title + " (" + p.topic + ") ";

        const toggle = document.createElement("button");
        toggle.textContent = "Toggle solved";
        toggle.addEventListener("click", () => toggleSolved(p.id));
        li.appendChild(toggle);

        const del = document.createElement("button");
        del.textContent = "Delete";
        del.addEventListener("click", () => deleteProblem(p.id));
        li.appendChild(del);

        list.appendChild(li);
    });
    loadStats();
}

async function loadStats() {
    const res = await fetch(API + "/stats/topics");
    if (!res.ok) return;
    const stats = await res.json();
    const box = document.getElementById("stats");
    box.innerHTML = "";
    stats.forEach(s => {
        const div = document.createElement("div");
        div.textContent = s.topic + ": " + s.solved + "/" + s.total + " solved (" + s.percent_solved + "%)";
        box.appendChild(div);
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

async function toggleSolved(id) {
    const res = await fetch(API + "/problems/" + id, { method: "PATCH" });
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