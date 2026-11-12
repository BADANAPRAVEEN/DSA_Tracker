const API =
    location.hostname === "127.0.0.1" || location.hostname === "localhost"
        ? "http://127.0.0.1:8000"
        : "https://dsa-tracker-wakr.onrender.com";

const list = document.getElementById("list");
const message = document.getElementById("message");
let messageTimer;

function showMessage(text, isError = true) {
    message.textContent = text;
    message.className = "msg " + (isError ? "error" : "ok");
    clearTimeout(messageTimer);
    messageTimer = setTimeout(() => {
        message.textContent = "";
        message.className = "msg";
    }, 4000);
}

function filterQuery() {
    const params = new URLSearchParams();
    const search = document.getElementById("f-search").value.trim();
    const topic = document.getElementById("f-topic").value.trim();
    const difficulty = document.getElementById("f-difficulty").value;
    const solved = document.getElementById("f-solved").value;
    if (search) params.set("search", search);
    if (topic) params.set("topic", topic);
    if (difficulty) params.set("difficulty", difficulty);
    if (solved) params.set("solved", solved);
    return params.toString();
}

async function loadProblems() {
    try {
        const qs = filterQuery();
        const res = await fetch(API + "/problems" + (qs ? "?" + qs : ""));
        if (!res.ok) {
            showMessage("Could not load problems (error " + res.status + ").");
            return;
        }
        const problems = await res.json();

        list.innerHTML = "";
        if (problems.length === 0) {
            list.innerHTML = "<li>No problems match.</li>";
            return;
        }

        problems.forEach(p => {
            const li = document.createElement("li");

            const main = document.createElement("div");
            main.textContent =
                (p.solved ? "✅ " : "⬜ ") + p.title + " (" + p.topic + ") ";

            const badge = document.createElement("span");
            badge.textContent = p.difficulty;
            badge.className = "badge " + p.difficulty.toLowerCase();
            main.appendChild(badge);

            if (p.link && /^https?:\/\//i.test(p.link)) {
                const a = document.createElement("a");
                a.href = p.link;
                a.textContent = " open";
                a.target = "_blank";
                a.rel = "noopener noreferrer";
                main.appendChild(a);
            }
            li.appendChild(main);

            if (p.notes) {
                const small = document.createElement("small");
                small.textContent = p.notes;
                li.appendChild(small);
            }

            const toggle = document.createElement("button");
            toggle.textContent = "Toggle solved";
            toggle.addEventListener("click", () => toggleSolved(p.id));
            li.appendChild(toggle);

            const del = document.createElement("button");
            del.textContent = "Delete";
            del.className = "danger";
            del.addEventListener("click", () => deleteProblem(p.id));
            li.appendChild(del);

            list.appendChild(li);
        });
    } catch (err) {
        showMessage("Cannot reach the server. If it was idle, wait a minute and try again.");
    }
}

async function loadStats() {
    try {
        const res = await fetch(API + "/stats/topics");
        if (!res.ok) return;
        const stats = await res.json();
        const box = document.getElementById("stats");
        box.innerHTML = "";
        stats.forEach(s => {
            const div = document.createElement("div");
            div.textContent =
                s.topic + ": " + s.solved + "/" + s.total + " solved (" + s.percent_solved + "%)";
            box.appendChild(div);
        });
    } catch (err) {
        /* stats are optional, so fail quietly */
    }
}

function refresh() {
    loadProblems();
    loadStats();
}

async function addProblem() {
    const title = document.getElementById("title").value.trim();
    const topic = document.getElementById("topic").value.trim();
    if (!title || !topic) {
        showMessage("Please enter a title and a topic.");
        return;
    }
    try {
        const res = await fetch(API + "/problems", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title: title,
                topic: topic,
                difficulty: document.getElementById("difficulty").value,
                link: document.getElementById("link").value.trim(),
                notes: document.getElementById("notes").value.trim(),
            }),
        });
        if (!res.ok) {
            showMessage(res.status === 422
                ? "Some of the values are not valid."
                : "Could not add the problem (error " + res.status + ").");
            return;
        }
        ["title", "topic", "link", "notes"].forEach(id => {
            document.getElementById(id).value = "";
        });
        showMessage("Problem added.", false);
        refresh();
    } catch (err) {
        showMessage("Cannot reach the server. Try again in a minute.");
    }
}

async function toggleSolved(id) {
    try {
        const res = await fetch(API + "/problems/" + id, { method: "PATCH" });
        if (!res.ok) { showMessage("Could not update (error " + res.status + ")."); return; }
        refresh();
    } catch (err) {
        showMessage("Cannot reach the server.");
    }
}

async function deleteProblem(id) {
    try {
        const res = await fetch(API + "/problems/" + id, { method: "DELETE" });
        if (!res.ok) { showMessage("Could not delete (error " + res.status + ")."); return; }
        refresh();
    } catch (err) {
        showMessage("Cannot reach the server.");
    }
}

function debounce(fn, delay) {
    let timer;
    return () => {
        clearTimeout(timer);
        timer = setTimeout(fn, delay);
    };
}

document.getElementById("add").addEventListener("click", addProblem);
document.getElementById("f-search").addEventListener("input", debounce(loadProblems, 300));
document.getElementById("f-topic").addEventListener("input", debounce(loadProblems, 300));
document.getElementById("f-difficulty").addEventListener("change", loadProblems);
document.getElementById("f-solved").addEventListener("change", loadProblems);

refresh();