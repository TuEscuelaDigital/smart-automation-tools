import json
import logging
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
LOG_PATH = BASE_DIR / "monitor.log"
REQUEST_TIMEOUT_SECONDS = 10


def setup_logging():
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    interval = config.get("interval_seconds")
    urls = config.get("urls")

    if not isinstance(interval, int) or interval <= 0:
        raise ValueError("config.json must define a positive integer interval_seconds")

    if not isinstance(urls, list) or not urls:
        raise ValueError("config.json must define a non-empty urls list")

    for url in urls:
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL in config.json: {url}")

    return urls, interval


def load_telegram_settings():
    load_dotenv(BASE_DIR / ".env")

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in the .env file"
        )

    return bot_token, chat_id


def send_telegram_message(bot_token, chat_id, message):
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    try:
        response = requests.post(api_url, data=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        logging.info("Telegram alert sent successfully")
    except requests.RequestException as exc:
        logging.error("Failed to send Telegram alert: %s", exc)


def check_url(url):
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        if 200 <= response.status_code < 300:
            return True, f"HTTP {response.status_code}"
        return False, f"HTTP {response.status_code}"
    except requests.Timeout:
        return False, "Request timed out"
    except requests.RequestException as exc:
        return False, str(exc)


def monitor_services(urls, interval, bot_token, chat_id):
    service_states = {url: None for url in urls}

    logging.info("Service monitor started. Checking %d URL(s).", len(urls))

    while True:
        for url in urls:
            is_up, status = check_url(url)
            previous_state = service_states[url]
            service_states[url] = is_up

            if is_up:
                logging.info("%s is up: %s", url, status)
                if previous_state is False:
                    message = f"RECOVERY: {url} is back up ({status})."
                    logging.info(message)
                    send_telegram_message(bot_token, chat_id, message)
            else:
                logging.warning("%s is down: %s", url, status)
                if previous_state is not False:
                    message = f"ALERT: {url} is down ({status})."
                    logging.warning(message)
                    send_telegram_message(bot_token, chat_id, message)

        time.sleep(interval)


def main():
    setup_logging()

    try:
        urls, interval = load_config()
        bot_token, chat_id = load_telegram_settings()
        monitor_services(urls, interval, bot_token, chat_id)
    except Exception as exc:
        logging.exception("Service monitor stopped: %s", exc)
        raise


if __name__ == "__main__":
    main()
