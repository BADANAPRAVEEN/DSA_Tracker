from datetime import datetime, timedelta, timezone

from database import get_db


def utc_today():
    # The database uses UTC dates, so the tests must too
    return datetime.now(timezone.utc).date()


def solved_problem(client, headers):
    problem = client.post(
        "/problems", json={"title": "Scheduler test", "topic": "Graphs"}, headers=headers
    ).json()
    return client.patch(f"/problems/{problem['id']}", headers=headers).json()


def force_due_today(problem_id):
    with get_db() as conn:
        conn.execute("UPDATE problems SET next_review = CURRENT_DATE WHERE id = %s", (problem_id,))


def review(client, headers, problem_id, remembered):
    return client.post(
        f"/problems/{problem_id}/review", json={"remembered": remembered}, headers=headers
    )


def test_solved_sample_problems_are_due_on_signup(client, user):
    due = client.get("/problems/due", headers=user["headers"]).json()
    assert sorted(p["title"] for p in due) == ["Binary Search", "Two Sum"]


def test_marking_solved_schedules_review_for_tomorrow(client, user):
    problem = solved_problem(client, user["headers"])
    assert problem["next_review"] == str(utc_today() + timedelta(days=1))
    due_ids = [p["id"] for p in client.get("/problems/due", headers=user["headers"]).json()]
    assert problem["id"] not in due_ids


def test_marking_unsolved_clears_the_schedule(client, user):
    problem = solved_problem(client, user["headers"])
    back = client.patch(f"/problems/{problem['id']}", headers=user["headers"]).json()
    assert back["solved"] is False
    assert back["next_review"] is None


def test_remembering_pushes_review_out_to_three_days(client, user):
    problem = solved_problem(client, user["headers"])
    force_due_today(problem["id"])
    res = review(client, user["headers"], problem["id"], True)
    assert res.status_code == 200
    assert res.json()["review_stage"] == 1
    assert res.json()["next_review"] == str(utc_today() + timedelta(days=3))


def test_forgetting_resets_to_tomorrow(client, user):
    problem = solved_problem(client, user["headers"])
    review(client, user["headers"], problem["id"], True)
    review(client, user["headers"], problem["id"], True)
    res = review(client, user["headers"], problem["id"], False)
    assert res.json()["review_stage"] == 0
    assert res.json()["next_review"] == str(utc_today() + timedelta(days=1))


def test_interval_stops_growing_at_thirty_days(client, user):
    problem = solved_problem(client, user["headers"])
    for _ in range(8):
        res = review(client, user["headers"], problem["id"], True)
    assert res.json()["review_stage"] == 4
    assert res.json()["next_review"] == str(utc_today() + timedelta(days=30))


def test_cannot_review_an_unsolved_problem(client, user):
    problem = client.post(
        "/problems", json={"title": "Not solved", "topic": "Graphs"}, headers=user["headers"]
    ).json()
    assert review(client, user["headers"], problem["id"], True).status_code == 409


def test_cannot_review_someone_elses_problem(client, make_user):
    alice = make_user()
    bob = make_user()
    problem = solved_problem(client, alice["headers"])
    assert review(client, bob["headers"], problem["id"], True).status_code == 404


def test_scheduler_routes_require_a_token(client):
    assert client.get("/problems/due").status_code == 401
    assert client.post("/problems/1/review", json={"remembered": True}).status_code == 401