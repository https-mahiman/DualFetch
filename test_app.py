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


def test_youtube_requires_cookie_file(monkeypatch):
    import app as app_module

    monkeypatch.delenv('COOKIE_FILE', raising=False)
    monkeypatch.delenv('YOUTUBE_COOKIES', raising=False)
    monkeypatch.setattr(app_module, 'get_cookie_file', lambda: None)

    client = app_module.app.test_client()
    response = client.post('/download', json={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'type': 'video'})

    assert response.status_code == 403
    assert 'cookies' in response.get_json()['error'].lower()
