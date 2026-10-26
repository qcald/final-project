"""Signup behavior that isn't a safety defense."""

import config


def test_new_users_start_friends_with_the_default_friend(client, monkeypatch):
    monkeypatch.setattr(config, "DEFAULT_FRIEND", "maya")
    res = client.post("/api/auth/register", json={"username": "newbie", "email": "newbie@example.com",
                                                  "display_name": "Newbie", "password": "longenough"})
    headers = {"Authorization": f"Bearer {res.json()['token']}"}
    friends = client.get("/api/friends", headers=headers).json()["friends"]
    assert [f["username"] for f in friends] == ["maya"]
