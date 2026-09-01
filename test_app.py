import importlib


def test_home_route():
    import app as app_module

    client = app_module.app.test_client()
    response = client.get('/')

    assert response.status_code == 200
    assert response.get_json()['status'] == 'online'


def test_port_uses_environment(monkeypatch):
    monkeypatch.setenv('PORT', '8080')
    import app as app_module

    importlib.reload(app_module)

    assert app_module.PORT == 8080
