Can this work also 
import os
import datetime
import threading

from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from telegram.request import HTTPXRequest


# =========================================================
# RENDER WEB SERVER
# =========================================================

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Husaraaj Recruitment Bot is running!"


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


# =========================================================
# CONFIG
# =========================================================

TOKEN = os.getenv("BOT_TOKEN", "8714999222:AAGvQiydKHeXAKVyRfnV6SE6J1loAdgYCiE")

ADMIN_ID = 1456630398

# Conversation states
NAME, AGE, PHONE, LOCATION, PASSPORT, EXPERIENCE, CV = range(7)


# =========================================================
# START MENU
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(
        f"New user: {update.effective_user.first_name} "
        f"ID: {update.effective_user.id}"
    )

    keyboard = [
        [InlineKeyboardButton("💼 JOBS AVAILABLE", callback_data="jobs_list")],
        [InlineKeyboardButton("📞 CONTACT US", callback_data="contact")],
    ]

    text = (
        "Welcome to Husaraaj Recruitment Agency!\n\n"
        "Your trusted partner for jobs abroad.\n\n"
        "Choose an option:"
    )

    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# =========================================================
# MENU
# =========================================================

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "jobs_list":

        keyboard = [
            [InlineKeyboardButton("🇶🇦 QATAR Jobs", callback_data="jobs_qatar")],
            [InlineKeyboardButton("🇸🇦 SAUDI Jobs", callback_data="jobs_saudi")],
            [InlineKeyboardButton("🇦🇪 DUBAI Jobs", callback_data="jobs_dubai")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_menu")],
        ]

        await query.message.edit_text(
            "Select Country:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data.startswith("jobs_"):

        country = query.data.split("_")[1].upper()

        keyboard = [
            [
                InlineKeyboardButton(
                    f"✅ Apply for {country}",
                    callback_data=f"apply_{country}",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="jobs_list",
                )
            ],
        ]

        await query.message.edit_text(
            f"Jobs available in {country}:\n"
            "- House Maid\n"
            "- Driver\n"
            "- Cleaner\n"
            "- Security\n\n"
            "Click Apply:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data.startswith("apply_"):

        context.user_data["country"] = query.data.split("_")[1]

        await query.message.edit_text(
            "Great! Let's start your application.\n\n"
            "What is your FULL NAME?"
        )

        return NAME

    elif query.data == "back_menu":

        await start(update, context)

    elif query.data == "contact":

        await query.message.edit_text(
            "📞 Contact Husaraaj:\n"
            "+256 700 000 000\n"
            "Location: Kampala, Uganda",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="back_menu",
                        )
                    ]
                ]
            ),
        )


# =========================================================
# APPLICATION
# =========================================================

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["name"] = update.message.text

    await update.message.reply_text(
        "How old are you? (Enter Age)"
    )

    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["age"] = update.message.text

    await update.message.reply_text(
        "What is your Phone Number?"
    )

    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["phone"] = update.message.text

    await update.message.reply_text(
        "Where do you live? (District)"
    )

    return LOCATION


async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["location"] = update.message.text

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Yes",
                callback_data="passport_yes",
            ),
            InlineKeyboardButton(
                "❌ No",
                callback_data="passport_no",
            ),
        ]
    ]

    await update.message.reply_text(
        "Do you have a Passport?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return PASSPORT


async def get_passport(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data["passport"] = query.data.split("_")[1]

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Yes",
                callback_data="exp_yes",
            ),
            InlineKeyboardButton(
                "❌ No",
                callback_data="exp_no",
            ),
        ]
    ]

    await query.message.edit_text(
        "Do you have experience abroad?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return EXPERIENCE


async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data["experience"] = query.data.split("_")[1]

    await query.message.edit_text(
        "Last step: Send your CV / Photo / or write about yourself"
    )

    return CV


async def get_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    data = context.user_data

    admin_text = (
        "🔥 NEW APPLICATION 🔥\n\n"
        f"Country: {data.get('country')}\n"
        f"Name: {data.get('name')}\n"
        f"Age: {data.get('age')}\n"
        f"Phone: {data.get('phone')}\n"
        f"Location: {data.get('location')}\n"
        f"Passport: {data.get('passport')}\n"
        f"Experience: {data.get('experience')}\n\n"
        f"From: {user.first_name} ID: {user.id}\n"
        f"Time: {datetime.datetime.now()}"
    )

    try:

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
        )

        if update.message.document or update.message.photo:

            await context.bot.forward_message(
                chat_id=ADMIN_ID,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
            )

        elif update.message.text:

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"CV Text: {update.message.text}",
            )

    except Exception as e:

        print(f"Failed to send to admin: {e}")

    await update.message.reply_text(
        "✅ Application Received!\n\n"
        "Husaraaj team will contact you soon. Thank you!"
    )

    await start(update, context)

    return ConversationHandler.END


# =========================================================
# CANCEL
# =========================================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Cancelled. Type /start to begin again."
    )

    return ConversationHandler.END


# =========================================================
# MAIN
# =========================================================

def main():

    # Start Flask web server for Render
    threading.Thread(
        target=run_web_server,
        daemon=True,
    ).start()

    request = HTTPXRequest(
        connection_pool_size=20,
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0,
    )

    app = (
        Application.builder()
        .token(TOKEN)
        .request(request)
        .build()
    )

    # Conversation handler
    conv_handler = ConversationHandler(

        entry_points=[
            CallbackQueryHandler(
                handle_menu,
                pattern="^apply_",
            )
        ],

        states={

            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_name,
                )
            ],

            AGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_age,
                )
            ],

            PHONE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_phone,
                )
            ],

            LOCATION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_location,
                )
            ],

            PASSPORT: [
                CallbackQueryHandler(
                    get_passport,
                    pattern="^passport_",
                )
            ],

            EXPERIENCE: [
                CallbackQueryHandler(
                    get_experience,
                    pattern="^exp_",
                )
            ],

            CV: [
                MessageHandler(
                    filters.TEXT
                    | filters.Document.ALL
                    | filters.PHOTO,
                    get_cv,
                )
            ],
        },

        fallbacks=[
            CommandHandler(
                "cancel",
                cancel,
            )
        ],
    )

    # Commands
    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    # Normal menu buttons
    app.add_handler(
        CallbackQueryHandler(
            handle_menu,
            pattern="^(jobs_|back_menu|contact)",
        )
    )

    # Application conversation
    app.add_handler(conv_handler)

    print("Husaraaj Bot is running...")
    print("Telegram bot is connected.")
    print("Render web server is running.")

    app.run_polling()


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()