from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.config import TELEGRAM_TOKEN
from bot.handlers import (
    start,
    handle_message,
    handle_voice,
    miniapp,
    handle_web_app_data,
    error_handler,
    voice_on,
    voice_off,
    pomodoro,
    progress,
    handle_button_press,
)

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("Telegram token not found. Please set the TELEGRAM_TOKEN environment variable.")

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_press))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))

    application.add_error_handler(error_handler)

    application.run_polling()

if __name__ == "__main__":
    main()
