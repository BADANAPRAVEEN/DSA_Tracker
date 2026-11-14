const API =
    location.hostname === "127.0.0.1" || location.hostname === "localhost"
        ? "http://127.0.0.1:8000"
        : "https://dsa-tracker-wakr.onrender.com";

const list = document.getElementById("list");
const dueList = document.getElementById("due-list");
const message = document.getElementById("message");
const authMessage = document.getElementById("auth-message");
let messageTimer;

/* ---------- token storage ---------- */

function getToken() {
    try { return localStorage.getItem("token"); } catch (e) { return null; }
}

function saveSession(token, email) {
    try {
        localStorage.setItem("token", token);
        localStorage.setItem("email", email);
    } catch (e) { /* storage unavailable */ }
}

function clearSession() {
    try {
        localStorage.removeItem("token");
        localStorage.removeItem("email");
    } catch (e) { /* ignore */ }
}

/* ---------- messages ---------- */

function showMessage(text, isError = true) {
    message.textContent = text;
    message.className = "msg " + (isError ? "error" : "ok");
    clearTimeout(messageTimer);
    messageTimer = setTimeout(() => {
        message.textContent = "";
        message.className = "msg";
    }, 4000);
}

function showAuthMessage(text, isError = true) {
    authMessage.textContent = text;
    authMessage.className = "msg " + (isError ? "error" : "ok");
}

/* ---------- views ---------- */

function updateView() {
    const loggedIn = !!getToken();
    document.getElementById("auth-section").classList.toggle("hidden", loggedIn);
    document.getElementById("app-section").classList.toggle("hidden", !loggedIn);
    if (loggedIn) {
        let email = "";
        try { email = localStorage.getItem("email") || ""; } catch (e) { /* ignore */ }
        document.getElementById("user-email").textContent = email;
        refresh();
    }
}

function logout(text) {
    clearSession();
    list.innerHTML = "";
    dueList.innerHTML = "";
    document.getElementById("stats").innerHTML = "";
    updateView();
    if (text) showAuthMessage(text);
}

/* ---------- fetch wrapper: adds the token to every request ---------- */

async function authFetch(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    const token = getToken();
    if (token) headers["Authorization"] = "Bearer " + token;

    const res = await fetch(API + path, { ...options, headers });

    if (res.status === 401) {
        logout("Your session has expired. Please log in again.");
    }
    return res;
}

/* ---------- signup and login ---------- */

async function sendAuth(path, email, password) {
    return fetch(API + "/auth" + path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, password: password }),
    });
}

async function login(email, password) {
    const res = await sendAuth("/login", email, password);
    if (!res.ok) {
        showAuthMessage(res.status === 401
            ? "Incorrect email or password."
            : "Could not log in (error " + res.status + ").");
        return;
    }
    const data = await res.json();
    saveSession(data.access_token, email.trim().toLowerCase());
    document.getElementById("auth-password").value = "";
    showAuthMessage("");
    updateView();
}

async function handleLogin() {
    const email = document.getElementById("auth-email").value.trim();
    const password = document.getElementById("auth-password").value;
    if (!email || !password) {
        showAuthMessage("Please enter your email and password.");
        return;
    }
    try {
        await login(email, password);
    } catch (err) {
        showAuthMessage("Cannot reach the server. If it was idle, wait a minute and try again.");
    }
}

async function handleSignup() {
    const email = document.getElementById("auth-email").value.trim();
    const password = document.getElementById("auth-password").value;
    if (!email || !password) {
        showAuthMessage("Please enter an email and a password.");
        return;
    }
    try {
        const res = await sendAuth("/signup", email, password);
        if (res.status === 409) {
            showAuthMessage("That email is already registered. Try logging in.");
            return;
        }
        if (res.status === 422) {
            showAuthMessage("Enter a valid email and a password of 8 to 64 characters.");
            return;
        }
        if (!res.ok) {
            showAuthMessage("Could not sign up (error " + res.status + ").");
            return;
        }
        await login(email, password);
    } catch (err) {
        showAuthMessage("Cannot reach the server. If it was idle, wait a minute and try again.");
    }
}

/* ---------- problems ---------- */

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
        const res = await authFetch("/problems" + (qs ? "?" + qs : ""));
        if (!res.ok) {
            if (res.status !== 401) showMessage("Could not load problems (error " + res.status + ").");
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
        const res = await authFetch("/stats/topics");
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

async function loadDue() {
    try {
        const res = await authFetch("/problems/due");
        if (!res.ok) return;
        const due = await res.json();

        dueList.innerHTML = "";
        if (due.length === 0) {
            dueList.innerHTML = "<li>Nothing due today. 🎉</li>";
            return;
        }

        due.forEach(p => {
            const li = document.createElement("li");

            const main = document.createElement("div");
            main.textContent = p.title + " (" + p.topic + ") ";
            const badge = document.createElement("span");
            badge.textContent = p.difficulty;
            badge.className = "badge " + p.difficulty.toLowerCase();
            main.appendChild(badge);
            li.appendChild(main);

            const yes = document.createElement("button");
            yes.textContent = "Remembered";
            yes.addEventListener("click", () => reviewProblem(p.id, true));
            li.appendChild(yes);

            const no = document.createElement("button");
            no.textContent = "Forgot";
            no.className = "danger";
            no.addEventListener("click", () => reviewProblem(p.id, false));
            li.appendChild(no);

            dueList.appendChild(li);
        });
    } catch (err) {
        /* the due list is optional, so fail quietly */
    }
}

async function reviewProblem(id, remembered) {
    try {
        const res = await authFetch("/problems/" + id + "/review", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ remembered: remembered }),
        });
        if (!res.ok) {
            if (res.status !== 401) showMessage("Could not save the review (error " + res.status + ").");
            return;
        }
        showMessage(remembered
            ? "Nice! You'll see it again later."
            : "No problem, you'll see it again tomorrow.", false);
        refresh();
    } catch (err) {
        showMessage("Cannot reach the server.");
    }
}

function refresh() {
    loadProblems();
    loadStats();
    loadDue();
}

async function addProblem() {
    const title = document.getElementById("title").value.trim();
    const topic = document.getElementById("topic").value.trim();
    if (!title || !topic) {
        showMessage("Please enter a title and a topic.");
        return;
    }
    try {
        const res = await authFetch("/problems", {
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
            if (res.status === 401) return;
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
        const res = await authFetch("/problems/" + id, { method: "PATCH" });
        if (!res.ok) {
            if (res.status !== 401) showMessage("Could not update (error " + res.status + ").");
            return;
        }
        refresh();
    } catch (err) {
        showMessage("Cannot reach the server.");
    }
}

async function deleteProblem(id) {
    try {
        const res = await authFetch("/problems/" + id, { method: "DELETE" });
        if (!res.ok) {
            if (res.status !== 401) showMessage("Could not delete (error " + res.status + ").");
            return;
        }
        refresh();
    } catch (err) {
        showMessage("Cannot reach the server.");
    }
}

/* ---------- events ---------- */

function debounce(fn, delay) {
    let timer;
    return () => {
        clearTimeout(timer);
        timer = setTimeout(fn, delay);
    };
}

document.getElementById("login-btn").addEventListener("click", handleLogin);
document.getElementById("signup-btn").addEventListener("click", handleSignup);
document.getElementById("logout-btn").addEventListener("click", () => logout(""));
document.getElementById("auth-password").addEventListener("keydown", e => {
    if (e.key === "Enter") handleLogin();
});

document.getElementById("add").addEventListener("click", addProblem);
document.getElementById("f-search").addEventListener("input", debounce(loadProblems, 300));
document.getElementById("f-topic").addEventListener("input", debounce(loadProblems, 300));
document.getElementById("f-difficulty").addEventListener("change", loadProblems);
document.getElementById("f-solved").addEventListener("change", loadProblems);

updateView();