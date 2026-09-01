import os
import sys
import shutil
from pathlib import Path

try:
    import browser_cookie3
except Exception as exc:  # pragma: no cover
    print(f"browser-cookie3 is required to export cookies: {exc}")
    sys.exit(1)


def export_cookies(output_path: str | None = None) -> str:
    output = Path(output_path) if output_path else Path(__file__).with_name('cookies.txt')
    output.parent.mkdir(parents=True, exist_ok=True)

    cookie_jar = None
    browser_names = ['chrome', 'chromium', 'brave', 'edge', 'firefox', 'safari']

    for browser in browser_names:
        try:
            cookie_jar = getattr(browser_cookie3, browser)()
            break
        except Exception:
            continue

    if cookie_jar is None:
        raise RuntimeError('No supported browser cookie store was found. Install Chrome/Edge/Firefox/Brave and log in before exporting cookies.')

    cookies = []
    for cookie in cookie_jar:
        if not cookie.name or not cookie.domain:
            continue
        cookies.append({
            'domain': cookie.domain,
            'host_only': cookie.domain.startswith('.'),
            'path': cookie.path,
            'secure': cookie.secure,
            'expires': cookie.expires,
            'name': cookie.name,
            'value': cookie.value,
            'http_only': cookie.has_nonstandard_attr('HttpOnly'),
        })

    with output.open('w', encoding='utf-8', newline='') as handle:
        for cookie in cookies:
            domain = cookie['domain']
            if domain.startswith('.'):
                domain = domain[1:]
            host_only = 'TRUE' if cookie['host_only'] else 'FALSE'
            secure = 'TRUE' if cookie['secure'] else 'FALSE'
            expires = int(cookie['expires']) if cookie['expires'] is not None else 0
            handle.write(
                f"{domain}\t{host_only}\t{cookie['path']}\t{secure}\t{expires}\t{cookie['name']}\t{cookie['value']}\n"
            )

    print(f"Cookies exported to: {output}")
    return str(output)


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else None
    export_cookies(target)
