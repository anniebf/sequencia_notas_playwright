from __future__ import annotations

import base64
from pathlib import Path

from anticaptchaofficial.imagecaptcha import imagecaptcha
from anticaptchaofficial.turnstileproxyless import turnstileProxyless


def save_data_url(data_url: str, destination: Path) -> None:
    _, encoded = data_url.split(",", 1)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(base64.b64decode(encoded))


def solve_image_captcha(token: str, image: Path) -> str:
    solver = imagecaptcha()
    solver.set_verbose(0)
    solver.set_key(token)
    result = solver.solve_and_return_solution(str(image))
    if not result or result == 0:
        raise RuntimeError(f"Anti-Captcha nao resolveu a imagem: {solver.error_code}")
    return str(result)


def solve_turnstile(token: str, url: str, site_key: str) -> str:
    solver = turnstileProxyless()
    solver.set_verbose(0)
    solver.set_key(token)
    solver.set_website_url(url)
    solver.set_website_key(site_key)
    result = solver.solve_and_return_solution()
    if not result or result == 0:
        raise RuntimeError(f"Anti-Captcha nao resolveu o Turnstile: {solver.error_code}")
    return str(result)
