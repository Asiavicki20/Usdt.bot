import os
import time
import asyncio
import threading
import feedparser

from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================
# BOT CONFIG
# =========================

TOKEN = "8928965950:AAFesOBWi6XLdJM8bnT8c8uk0i7YNiZnwFE"

CHANNEL_ID = -1003759969299

FEED_URL = FEED_URL = "https://cointelegraph.com/rss"

ADMIN_ID = 7012709444

posted_links = set()
waiting_for_hash = set()
user_data = {}

# =========================
# KEEP ALIVE WEB SERVER
# =========================

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app_web.run(host="0.0.0.0", port=port)

# =========================
# COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message:
        await update.message.reply_text(
            "Welcome to USDT Recovery-Receive Bot."
        )
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start\n/help\n/status\n/contact"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot is online ✅"
    )

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message:
        await update.message.reply_text(
            "Support request received."
        )

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "FAQ section."
    )
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message:
        await update.message.reply_text(
            "Support request received."
        )


async def security(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message:
        await update.message.reply_text(
            "Your transactions are protected with secure verification."
        )
async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send your wallet address."
    )

async def recovery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    waiting_for_hash.add(update.effective_user.id)

    await update.message.reply_text(
        "Send your transaction hash."
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Scanning transaction..."
    )

# =========================
# MESSAGE HANDLER
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

        if not update.effective_user:
            return

        if not update.message:
            return

        user_id = update.effective_user.id
        text = update.message.text

        # Recovery hash flow
        if user_id in waiting_for_hash:

            waiting_for_hash.remove(user_id)

            user_data[user_id] = {
                "txid": text,
                "waiting_wallet": True
            }

            await update.message.reply_text(
                "Now send your wallet address."
            )

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"New TXID from {user_id}:\n{text}"
            )

            return

        # Wallet flow
        if (
            user_id in user_data and
            user_data[user_id].get("waiting_wallet")
        ):

            wallet_address = text

            user_data[user_id]["wallet"] = wallet_address
            user_data[user_id]["waiting_wallet"] = False

            await update.message.reply_text(
                "Recovery request submitted ✅"
            )

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"Recovery Request\n\n"
                    f"User ID: {user_id}\n"
                    f"TXID: {user_data[user_id]['txid']}\n"
                    f"Wallet: {wallet_address}"
                )
            )

# =========================
# AUTO FEED
# =========================

def auto_feed(bot_app):

    while True:

        try:
            feed = feedparser.parse(FEED_URL)

            for entry in feed.entries[:5]:

                if entry.link not in posted_links:

                    message = (
                        f"📰 {entry.title}\n\n"
                        f"{entry.link}"
                    )

                    asyncio.run(
                        bot_app.bot.send_message(
                            chat_id=CHANNEL_ID,
                            text=message
                        )
                    )

                    posted_links.add(entry.link)

        except Exception as e:
            print("FEED ERROR:", e)

        time.sleep(300)

# =========================
# BUILD BOT
# =========================

bot_app = ApplicationBuilder().token(TOKEN).build()

# =========================
# HANDLERS
# =========================

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", help_command))
bot_app.add_handler(CommandHandler("status", status))
bot_app.add_handler(CommandHandler("contact", contact))
bot_app.add_handler(CommandHandler("support", contact))
bot_app.add_handler(CommandHandler("faq", faq))
bot_app.add_handler(CommandHandler("security", security))
bot_app.add_handler(CommandHandler("wallet", wallet))
bot_app.add_handler(CommandHandler("recovery", recovery))
bot_app.add_handler(CommandHandler("scan", scan))
bot_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

# =========================
# START WEB SERVER
# =========================

threading.Thread(
    target=run_web,
    daemon=True
).start()

# =========================
# START AUTO FEED
# =========================

threading.Thread(
    target=auto_feed,
    args=(bot_app,),
    daemon=True
).start()

# =========================
# RUN BOT
# =========================

print("Bot running...")

bot_app.run_polling(drop_pending_updates=True)