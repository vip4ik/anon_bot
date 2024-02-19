from app.data.config import Config


async def errors_handler(update, exception):
    error = f'Error: {exception}\nUpdate: {update}'
    # await update.bot.send_message("@" + Config.LOGS_DOMAIN, f"<code>{error}</code>")
