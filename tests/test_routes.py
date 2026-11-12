import sqlite3

from conftest import csrf_token
from test_documents import upload
from test_notes import create_note


def test_all_pages_and_local_assets(logged_client):
    for path in ("/", "/notes/", "/notes/new", "/documents/", "/documents/new"):
        response = logged_client.get(path)
        assert response.status_code == 200
        text = response.get_data(as_text=True)
        assert 'lang="es"' in text
        assert 'name="viewport"' in text
        assert 'https://' not in text and 'http://' not in text
    for path in ("/static/css/app.css", "/static/vendor/bootstrap.min.css"):
        assert logged_client.get(path).status_code == 200


def test_dashboard_counts_are_per_user(app, logged_client):
    create_note(logged_client)
    upload(logged_client)
    page = logged_client.get("/").get_data(as_text=True)
    assert page.count('class="metric">1</p>') == 2
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        conn.execute("UPDATE notes SET user_id = 2")
        conn.execute("UPDATE documents SET user_id = 2")
    page = logged_client.get("/").get_data(as_text=True)
    assert page.count('class="metric">0</p>') == 2


def test_empty_states_and_post_only_verification(logged_client):
    assert "Todavía no tienes notas" in logged_client.get("/notes/").get_data(as_text=True)
    assert "Carga tu primer documento" in logged_client.get("/documents/").get_data(as_text=True)
    assert logged_client.get("/documents/1/verify").status_code == 405
    assert logged_client.get("/documents/1/check-copy").status_code == 405


def test_request_body_limit(logged_client):
    token = csrf_token(logged_client, "/documents/new")
    response = logged_client.post("/documents/new", data={"csrf_token": token, "extra": "x" * (600 * 1024)})
    assert response.status_code == 413
