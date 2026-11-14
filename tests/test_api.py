from datetime import datetime, timedelta, timezone

import jwt
from routers.auth import ALGORITHM, SECRET_KEY


def add_problem(client, headers, **overrides):
    data = {"title": "Test problem", "topic": "Graphs", "difficulty": "Medium"}
    data.update(overrides)
    return client.post("/problems", json=data, headers=headers)


# ---------- signup ----------

def test_signup_creates_user_without_leaking_secrets(client, unique_email):
    email = unique_email()
    res = client.post("/auth/signup", json={"email": email, "password": "TestPass123"})
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == email
    assert "password" not in body
    assert "password_hash" not in body


def test_signup_duplicate_email_returns_409(client, user):
    res = client.post("/auth/signup", json={"email": user["email"], "password": "TestPass123"})
    assert res.status_code == 409


def test_signup_rejects_bad_input(client, unique_email):
    short_password = client.post("/auth/signup", json={"email": unique_email(), "password": "abc"})
    bad_email = client.post("/auth/signup", json={"email": "hello", "password": "TestPass123"})
    assert short_password.status_code == 422
    assert bad_email.status_code == 422


# ---------- login ----------

def test_login_success_returns_token(client, user):
    res = client.post("/auth/login", json={"email": user["email"], "password": user["password"]})
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"
    assert res.json()["access_token"]


def test_wrong_password_and_unknown_email_look_the_same(client, user, unique_email):
    wrong_password = client.post("/auth/login", json={"email": user["email"], "password": "WrongPass999"})
    unknown_email = client.post("/auth/login", json={"email": unique_email(), "password": "TestPass123"})
    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json()["detail"] == unknown_email.json()["detail"]


# ---------- tokens ----------

def test_problems_require_a_token(client):
    assert client.get("/problems").status_code == 401
    res = client.get("/problems", headers={"Authorization": "Bearer garbage"})
    assert res.status_code == 401


def test_expired_token_is_rejected(client):
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    res = client.get("/problems", headers={"Authorization": f"Bearer {expired}"})
    assert res.status_code == 401


def test_token_signed_with_wrong_key_is_rejected(client):
    forged = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        "a-completely-different-secret-key-0123456789",
        algorithm=ALGORITHM,
    )
    res = client.get("/problems", headers={"Authorization": f"Bearer {forged}"})
    assert res.status_code == 401


# ---------- problems ----------

def test_new_user_gets_four_sample_problems(client, user):
    res = client.get("/problems", headers=user["headers"])
    assert res.status_code == 200
    assert len(res.json()) == 4


def test_add_problem_and_see_it_in_the_list(client, user):
    res = add_problem(client, user["headers"], title="My new problem", difficulty="Hard")
    assert res.status_code == 201
    assert res.json()["difficulty"] == "Hard"
    titles = [p["title"] for p in client.get("/problems", headers=user["headers"]).json()]
    assert "My new problem" in titles


def test_add_problem_validation(client, user):
    bad_difficulty = add_problem(client, user["headers"], difficulty="Super")
    empty_title = add_problem(client, user["headers"], title="")
    assert bad_difficulty.status_code == 422
    assert empty_title.status_code == 422


def test_toggle_solved_flips_the_value(client, user):
    problem = add_problem(client, user["headers"]).json()
    assert problem["solved"] is False
    first = client.patch(f"/problems/{problem['id']}", headers=user["headers"])
    assert first.json()["solved"] is True
    second = client.patch(f"/problems/{problem['id']}", headers=user["headers"])
    assert second.json()["solved"] is False


def test_delete_then_delete_again(client, user):
    problem = add_problem(client, user["headers"]).json()
    first = client.delete(f"/problems/{problem['id']}", headers=user["headers"])
    second = client.delete(f"/problems/{problem['id']}", headers=user["headers"])
    assert first.status_code == 204
    assert second.status_code == 404


def test_filters_by_difficulty_and_search(client, user):
    add_problem(client, user["headers"], title="Filter Easy One", difficulty="Easy")
    add_problem(client, user["headers"], title="Filter Hard One", difficulty="Hard")

    hard = client.get("/problems", params={"difficulty": "Hard"}, headers=user["headers"]).json()
    assert len(hard) >= 1
    assert all(p["difficulty"] == "Hard" for p in hard)

    found = client.get("/problems", params={"search": "filter easy"}, headers=user["headers"]).json()
    assert [p["title"] for p in found] == ["Filter Easy One"]


def test_stats_show_weakest_topic_first(client, user):
    stats = client.get("/stats/topics", headers=user["headers"]).json()
    percents = [s["percent_solved"] for s in stats]
    assert percents == sorted(percents)
    assert stats[0]["topic"] == "Stack"


# ---------- authorization ----------

def test_users_cannot_touch_each_others_problems(client, make_user):
    alice = make_user()
    bob = make_user()
    problem = add_problem(client, alice["headers"], title="Alice private problem").json()

    bob_titles = [p["title"] for p in client.get("/problems", headers=bob["headers"]).json()]
    assert "Alice private problem" not in bob_titles

    assert client.delete(f"/problems/{problem['id']}", headers=bob["headers"]).status_code == 404
    assert client.patch(f"/problems/{problem['id']}", headers=bob["headers"]).status_code == 404

    alice_titles = [p["title"] for p in client.get("/problems", headers=alice["headers"]).json()]
    assert "Alice private problem" in alice_titles