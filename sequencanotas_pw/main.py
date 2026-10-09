from __future__ import annotations

import re
import sys
from pathlib import Path


from playwright.sync_api import Browser, BrowserContext, Page, TimeoutError, sync_playwright

if __package__:
    from .captcha import save_data_url, solve_image_captcha, solve_turnstile
    from .config import Config, load_config
    from .dates import gerar_intervalo_datas
    from .files import convert_download_to_csv, copy_to_production
    from .logging_utils import configure_logging
    from .oracle import retorno_cnpjs
else:
    # Permite executar este arquivo diretamente pelo PowerShell ou por um .bat.
    package_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(package_root))
    from sequencanotas_pw.captcha import save_data_url, solve_image_captcha, solve_turnstile
    from sequencanotas_pw.config import Config, load_config
    from sequencanotas_pw.dates import gerar_intervalo_datas
    from sequencanotas_pw.files import convert_download_to_csv, copy_to_production
    from sequencanotas_pw.logging_utils import configure_logging
    from sequencanotas_pw.oracle import retorno_cnpjs

LOGIN_URL = "https://www.sefaz.mt.gov.br/acesso/pages/login/login.xhtml"
CONSULT_URL = (
    "https://www.sefaz.mt.gov.br/nfe/pages/consultaemitidasrecebidas/"
    "consultaemitidasrecebidas.xhtml"
)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
TURNSTILE_SITE_KEY = "0x4AAAAAABpF5mikgYMo5Mk-"


def _first_visible(page: Page, selectors: list[str], timeout: int = 10):
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            locator.wait_for(state="visible", timeout=timeout * 1000)
            return locator
        except TimeoutError:
            continue
    raise TimeoutError(f"Nenhum seletor ficou visivel: {selectors}")


def _confirm_human(page: Page) -> None:
    checkbox = page.locator(
        "input[type='checkbox'][aria-label='Confirme que é humano']"
    ).first
    checkbox.wait_for(state="attached", timeout=10000)
    if not checkbox.is_checked():
        checkbox.check(force=True, timeout=5000)
    if not checkbox.is_checked():
        raise RuntimeError("O checkbox 'Confirme que é humano' nao foi marcado.")


def _solve_login_captcha(page: Page, config: Config, logger) -> None:
    image = page.locator('img[src^="data:image/"]').first
    if image.count():
        if not config.anti_captcha_token:
            raise RuntimeError("ANTI_CAPTCHA_TOKEN nao definido.")
        source = image.get_attribute("src")
        if source:
            image_path = config.captcha_dir / "captcha.png"
            save_data_url(source, image_path)
            answer = solve_image_captcha(config.anti_captcha_token, image_path)
            page.locator("#formLogin\\:inputCaptcha").fill(answer)
            _confirm_human(page)
            logger.info("Captcha de imagem resolvido e preenchido.")
            return

    container = page.locator("#captcha-container").first
    if container.count():
        if not config.anti_captcha_token:
            raise RuntimeError("ANTI_CAPTCHA_TOKEN nao definido.")
        site_key = None
        site_key_locator = page.locator("[data-sitekey]").first
        try:
            site_key = site_key_locator.get_attribute("data-sitekey", timeout=2000)
        except TimeoutError:
            logger.info(
                "O site key nao foi exposto no DOM; usando o site key configurado da SEFAZ."
            )
        site_key = site_key or TURNSTILE_SITE_KEY
        if site_key:
            token = solve_turnstile(config.anti_captcha_token, LOGIN_URL, site_key)
            response_field = page.locator('input[name="cf-turnstile-response"]').first
            response_field.evaluate(
                "(element, value) => { element.value = value; "
                "element.dispatchEvent(new Event('input', { bubbles: true })); "
                "element.dispatchEvent(new Event('change', { bubbles: true })); }",
                token,
            )
            if response_field.input_value() != token:
                raise RuntimeError("O token Turnstile nao foi aplicado ao formulario.")
            # Alguns carregamentos exibem o checkbox em um iframe; outros
            # escutam a interacao no container externo.
            widget_frame = page.locator(
                "iframe[title*='Turnstile'], iframe[title*='Cloudflare']"
            ).first
            try:
                widget_frame.click(timeout=3000, force=True)
            except TimeoutError:
                container.click(force=True)
            page.wait_for_timeout(1500)
            #_confirm_human(page)
            logger.info("Token Turnstile inserido e widget acionado.")
            return
    logger.info("Nenhum captcha de login visivel; seguindo com o formulario.")


def login(page: Page, config: Config, logger) -> None:
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    for attempt in range(1, 6):
        logger.info("Tentativa de login %s/5", attempt)
        try:
            _first_visible(
                page,
                ["#formLogin\\:inputLogin", "#captcha-container"],
            )
            _solve_login_captcha(page, config, logger)
            logger.info("Captcha validado; preenchendo as credenciais.")
            user_type = page.locator("#formLogin\\:selectTipoUsuario_label")
            user_type.wait_for(state="visible", timeout=10000)
            user_type.click()
            contabilista_option = page.locator("#formLogin\\:selectTipoUsuario_1")
            contabilista_option.wait_for(state="visible", timeout=10000)
            contabilista_option.click()
            logger.info("Tipo de usuario Contabilista selecionado.")
            login_input = page.locator("#formLogin\\:inputLogin")
            password_input = page.locator("#formLogin\\:inputSenha")
            login_input.wait_for(state="visible", timeout=10000)
            password_input.wait_for(state="visible", timeout=10000)
            login_input.fill(config.contabilista)
            password_input.fill(config.senha_contabilista)
            if password_input.input_value() != config.senha_contabilista:
                raise RuntimeError("A senha nao foi inserida no campo de login.")
            logger.info("Contabilista e senha preenchidos.")
            login_button = page.locator(
                "button:has-text('Efetuar Login'), "
                "input[type='submit'][value*='Efetuar Login']"
            ).first
            login_button.wait_for(state="visible", timeout=10000)
            login_button.click()
            try:
                password_input.fill(config.senha_contabilista)
                login_button.click()
            except Exception:
                pass
            logger.info("Formulario de login enviado.")

            error = page.locator(".ui-messages-error").first
            try:
                error.wait_for(state="visible", timeout=3000)
                text = error.inner_text().strip()
                if text:
                    logger.warning("SEFAZ recusou o login: %s", text)
                    if "Senha Inválida" in text:
                        raise RuntimeError(text)
                    page.reload(wait_until="domcontentloaded")
                    continue
            except TimeoutError:
                pass

            # O portal nem sempre renderiza o elemento ``#tst`` depois do
            # login. Nesse caso, o desaparecimento do formulario indica que
            # a navegacao autenticada foi concluida.
            page.wait_for_function(
                """() => {
                    const loggedArea = document.querySelector('#tst');
                    const loginForm = document.querySelector('#formLogin');
                    return Boolean(
                        (loggedArea && window.getComputedStyle(loggedArea).display !== 'none') ||
                        !loginForm ||
                        window.getComputedStyle(loginForm).display === 'none'
                    );
                }""",
                timeout=20000,
            )
            logger.info("Login efetuado com sucesso.")
            return
        except TimeoutError:
            logger.warning(
                "Tentativa %s nao concluiu; pagina atual: %s",
                attempt,
                page.url,
            )
            if attempt == 5:
                page.screenshot(path=str(config.log_dir / "login-timeout.png"), full_page=True)
                raise RuntimeError("Tempo esgotado durante o login.")
            page.reload(wait_until="domcontentloaded")
    raise RuntimeError("Nao foi possivel efetuar o login.")


def fill_query(page: Page, cnpj: str, start_date: str, end_date: str) -> None:
    document_type = page.locator(
        "xpath=//label[normalize-space()='Inscrição Estadual']"
    ).first
    document_type.wait_for(state="visible", timeout=10000)
    document_type.click()
    page.wait_for_timeout(500)

    document_option = page.locator(
        "xpath=//li[normalize-space()='CNPJ' and @role='option']"
    ).first
    document_option.wait_for(state="visible", timeout=10000)
    document_option.click()
    page.wait_for_timeout(700)

    input_cnpj = page.locator(
        "div.ui-panel-content.ui-widget-content input.ui-inputmask"
    ).first
    input_cnpj.wait_for(state="visible", timeout=10000)
    input_cnpj.click()
    input_cnpj.fill("")
    input_cnpj.type(cnpj, delay=60)
    input_cnpj.press("Tab")
    page.wait_for_timeout(500)


    dates = page.locator("input.hasDatepicker")
    dates.nth(0).wait_for(state="visible", timeout=10000)
    dates.nth(1).wait_for(state="visible", timeout=10000)

    for field, value, label in (
        (dates.nth(0), start_date, "data inicial"),
        (dates.nth(1), end_date, "data final"),
    ):

        field.click()
        field.fill("")
        field.type(value, delay=80)
        field.press("Tab")
        page.wait_for_timeout(600)


    page.wait_for_timeout(800)
    consult_button = page.get_by_role("button", name=re.compile("Consultar", re.I))
    consult_button.wait_for(state="visible", timeout=10000)
    consult_button.click()


def _query_error(page: Page, cnpj: str, logger) -> bool:
    messages = (
        ("Contabilista não representa", "O CNPJ nao representa o contabilista."),
        ("Documento deve ser informado", "O CNPJ nao foi informado no site."),
        ("Data inválida", "As datas da consulta foram rejeitadas."),
    )
    for text, description in messages:
        message = page.get_by_text(re.compile(text, re.I)).first
        try:
            message.wait_for(state="visible", timeout=3000)
        except TimeoutError:
            continue
        logger.error("%s: %s", cnpj, description)
        return True
    return False


def query_cnpj(
    context: BrowserContext,
    config: Config,
    logger,
    cnpj: str,
    start_date: str,
    end_date: str,
) -> None:
    page = context.new_page()
    try:
        logger.info("Iniciando consulta do CNPJ %s.", cnpj)
        page.goto(CONSULT_URL, wait_until="domcontentloaded")
        fill_query(page, cnpj, start_date, end_date)

        if _query_error(page, cnpj, logger):
            return

        export = page.get_by_text("Exportar para Excel", exact=True)
        export.wait_for(state="visible", timeout=30000)
        with page.expect_download(timeout=30000) as download_info:
            export.click()
        download = download_info.value
        temporary = config.download_dir / download.suggested_filename
        config.download_dir.mkdir(parents=True, exist_ok=True)
        download.save_as(temporary)
        try:
            csv_path = convert_download_to_csv(temporary, config.csv_dir, cnpj)
        except RuntimeError as exc:
            logger.error("%s: %s", cnpj, exc)
            return
        copy_to_production(csv_path, config.producao_dir)
        logger.info("CSV gerado para %s: %s", cnpj, csv_path)
    except TimeoutError:
        logger.exception("Tempo esgotado ao processar o CNPJ %s.", cnpj)
    finally:
        page.close()


def run(config: Config) -> None:
    logger = configure_logging(config.log_dir)
    start_date, end_date = gerar_intervalo_datas()
    cnpjs = retorno_cnpjs(config)
    logger.info("Processando %s CNPJs no periodo %s a %s.", len(cnpjs), start_date, end_date)
    with sync_playwright() as playwright:
        browser: Browser = playwright.chromium.launch(
            headless=config.headless,
            args=["--disable-popup-blocking"],
        )
        context = browser.new_context(
            accept_downloads=True,
            user_agent=USER_AGENT,
            viewport={"width": 1920, "height": 1080},
        )
        try:
            page = context.new_page()
            login(page, config, logger)
            for cnpj in cnpjs:
                query_cnpj(context, config, logger, cnpj, start_date, end_date)
        finally:
            context.close()
            browser.close()


def main() -> None:
    run(load_config())


if __name__ == "__main__":
    main()
