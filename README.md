# Telegram Task Management Bot

This is a Telegram bot for task management and productivity, built with Python and the `python-telegram-bot` library. It integrates with various AI models (GPT-4o, Claude-3.5-sonnet, Grok) and Google Calendar to help you manage your tasks effectively.

## Features

-   **AI Model Switching:** Switch between different AI models for task processing.
-   **Google Calendar Integration:** View events and create tasks in your Google Calendar.
-   **Speech-to-Text:** Transcribe voice messages using ElevenLabs API.
-   **Telegram Mini App Support:** A placeholder for integrating a Telegram Mini App.
-   **User Data Persistence:** User preferences and context are stored in a local SQLite database.

## Project Structure

```
.
├── bot/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── handlers.py
│   ├── gcal.py
│   ├── stt.py
│   └── storage.py
├── .env
├── requirements.txt
└── README.md
```

## Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment and install dependencies:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**

    Create a `.env` file in the root of the project and add the following, replacing the placeholder values with your actual keys:

    ```
    TELEGRAM_TOKEN="YOUR_TELEGRAM_TOKEN"
    OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
    ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY"
    GROK_API_KEY="YOUR_GROK_API_KEY"
    ELEVENLABS_API_KEY="YOUR_ELEVENLABS_API_KEY"
    MINI_APP_URL="https://your-mini-app-url.com"
    ```

4.  **Set up Google Calendar API credentials:**

    -   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    -   Create a new project.
    -   Enable the "Google Calendar API".
    -   Create credentials for a "Desktop application".
    -   Download the `credentials.json` file and place it in the root of the project directory.

    The first time you run the bot, you will be prompted to authorize the application. A `token.json` file will be created to store the access and refresh tokens. Make sure to add `credentials.json` and `token.json` to your `.gitignore` file if you are using version control.

## Running the Bot

To run the bot, execute the following command:

```bash
python -m bot.main
```

## Bot Commands

-   `/start`: Welcome message.
-   `/model [gpt/claude/grok]`: Switch between AI models.
-   `/miniapp`: Open the Telegram Mini App.

## Notes

-   The Grok model integration is a placeholder and requires a proper implementation with the Grok API.
-   The context management in `bot/models.py` and `bot/handlers.py` is a simplified implementation and may need to be extended for more complex scenarios.
-   Error handling is basic and can be improved with more specific error handling and logging.
-   The Google Calendar integration requires user authorization and may need additional setup depending on your specific needs.
