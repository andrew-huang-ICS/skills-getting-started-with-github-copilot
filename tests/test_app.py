from src.app import activities


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_with_expected_fields(client):
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert {"Chess Club", "Programming Class", "Gym Class"} <= set(data)
    for details in data.values():
        assert {"description", "schedule", "max_participants", "participants"} <= set(details)


def test_signup_adds_participant(client):
    email = "new.student@mergington.edu"
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities["Chess Club"]["participants"]


def test_signup_unknown_activity_returns_404(client):
    response = client.post("/activities/Nope/signup", params={"email": "a@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_returns_400(client):
    email = activities["Chess Club"]["participants"][0]
    before = list(activities["Chess Club"]["participants"])
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities["Chess Club"]["participants"] == before


def test_unregister_removes_participant(client):
    email = activities["Gym Class"]["participants"][0]
    response = client.delete("/activities/Gym Class/signup", params={"email": email})
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Gym Class"}
    assert email not in activities["Gym Class"]["participants"]


def test_unregister_unknown_activity_returns_404(client):
    response = client.delete("/activities/Nope/signup", params={"email": "a@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_not_signed_up_returns_404(client):
    response = client.delete(
        "/activities/Chess Club/signup", params={"email": "ghost@mergington.edu"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_signup_unregister_signup_roundtrip(client):
    email = "round.trip@mergington.edu"
    url = "/activities/Programming Class/signup"
    assert client.post(url, params={"email": email}).status_code == 200
    assert client.delete(url, params={"email": email}).status_code == 200
    assert email not in activities["Programming Class"]["participants"]
    assert client.post(url, params={"email": email}).status_code == 200
    assert activities["Programming Class"]["participants"].count(email) == 1


def test_state_is_reset_between_tests(client):
    # Earlier tests mutate activities; the autouse fixture must restore the seed data.
    assert "new.student@mergington.edu" not in activities["Chess Club"]["participants"]
    assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
