# Service Monitor

`service_monitor.py` monitors a configured list of URLs and sends Telegram alerts when a service goes down or recovers.

The script:

- Reads monitored URLs and the polling interval from `config.json`
- Checks each URL with an HTTP GET request every configured interval
- Treats non-2xx HTTP responses and request timeouts as failures
- Sends Telegram alerts using the Telegram Bot API
- Sends recovery notifications when a previously failing service comes back up
- Logs checks, alerts, recoveries, and errors to `monitor.log`

## Files

- `service_monitor.py` - the monitoring script
- `config.json` - URLs and check interval
- `.env.example` - example environment variables for Telegram credentials
- `requirements.txt` - Python package dependencies
- `monitor.log` - created automatically when the script runs

## Requirements

- Python 3.8 or newer
- `requests`
- `python-dotenv`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.json`:

```json
{
  "interval_seconds": 60,
  "urls": [
    "https://example.com",
    "https://httpbin.org/status/200",
    "https://www.python.org"
  ]
}
```

- `interval_seconds` controls how often the URLs are checked.
- `urls` is the list of services to monitor.

Create a `.env` file from the example:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

```env
TELEGRAM_BOT_TOKEN=your_real_bot_token
TELEGRAM_CHAT_ID=your_real_chat_id
```

## Getting a Telegram Bot Token

1. Open Telegram and search for `@BotFather`.
2. Start a chat with BotFather.
3. Send `/newbot`.
4. Follow the prompts to choose a bot name and username.
5. BotFather will return a bot token. Use that value for `TELEGRAM_BOT_TOKEN`.

Keep the token private. Anyone with the token can control your bot.

## Getting a Telegram Chat ID

1. Send a message to your new bot in Telegram.
2. Open this URL in a browser, replacing `<BOT_TOKEN>` with your real token:

```text
https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
```

3. Look for the `chat` object in the JSON response.
4. Copy the `id` value and use it for `TELEGRAM_CHAT_ID`.

For a group chat, add the bot to the group, send a message in the group, then call `getUpdates` and use the group chat ID.

## Running the Monitor

From inside the `service-monitor` folder:

```bash
python service_monitor.py
```

The script runs continuously until stopped with `Ctrl+C`.

Logs are written to:

```text
monitor.log
```

## Alert Behavior

The monitor keeps an in-memory status for each URL:

- If a URL fails for the first time, it sends a down alert.
- If the URL keeps failing, it logs the failure but does not send repeated alerts.
- If the URL recovers after being down, it sends a recovery notification.
