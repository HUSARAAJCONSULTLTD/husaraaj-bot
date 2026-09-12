import os
import datetime
import threading
import requests

from flask import Flask, request

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
    return "Husaraaj Recruitment Bot is running!", 200


@web_app.route("/health")
def health():
    return "OK", 200


# =========================================================
# WHATSAPP CONFIGURATION
# =========================================================

WHATSAPP_ACCESS_TOKEN = os.getenv(
    "WHATSAPP_ACCESS_TOKEN",
    "EAAoydwzwImgBSaaBQlBJK74JfT9wq5VZANHCf4db1U471Lwv4CCQZAZCuZBzWTdYKqKF0cQxa6gddRBvf7gte6jtcy0am1ovkMK0w5XhiClQwTuKVsZALIjxWz6P304UgsDZBflxi1XeeoSSnepB0Y3ETNws7j092D5ZCZBaIsWOFXcQCsdjwTZBNylYExQbzCnDFZBUMXIDh8AhwTcM3tZBUgiQUZA2suBdNAFNlkbuQAkxx84F5wnKC83m0MK7fHHxReJu9SBTiZBMFKZAwZCBAZAikZBDNyFvA"
)

WHATSAPP_PHONE_NUMBER_ID = os.getenv(
    "WHATSAPP_PHONE_NUMBER_ID",
    "1254946521043354"
)

WHATSAPP_VERIFY_TOKEN = os.getenv(
    "WHATSAPP_VERIFY_TOKEN",
    "2175076963059453"
)

# Husaraaj admin WhatsApp number
# Use international format without +
WHATSAPP_ADMIN_NUMBER = os.getenv(
    "WHATSAPP_ADMIN_NUMBER",
    "256730465869"
)

WHATSAPP_API_VERSION = os.getenv(
    "WHATSAPP_API_VERSION",
    "v23.0"
)


# =========================================================
# WHATSAPP API FUNCTION
# =========================================================

def whatsapp_url():
    return (
        f"https://graph.facebook.com/"
        f"{WHATSAPP_API_VERSION}/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )


def send_whatsapp_message(phone, text):

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    data = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {
            "body": text
        }
    }

    try:
        response = requests.post(
            whatsapp_url(),
            headers=headers,
            json=data,
            timeout=30
        )

        print(
            "WhatsApp send:",
            response.status_code,
            response.text
        )

        return response.ok

    except Exception as e:
        print("WhatsApp send error:", e)
        return False


# =========================================================
# WHATSAPP CONVERSATION STORAGE
# =========================================================

whatsapp_users = {}


# =========================================================
# WHATSAPP WEBHOOK VERIFICATION
# =========================================================

@web_app.route("/webhook", methods=["GET"])
def verify_whatsapp_webhook():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:

        print("WhatsApp webhook verified successfully.")

        return challenge, 200

    print("WhatsApp webhook verification failed.")

    return "Verification failed", 403


# =========================================================
# WHATSAPP WEBHOOK RECEIVE
# =========================================================

@web_app.route("/webhook", methods=["POST"])
def whatsapp_webhook():

    data = request.get_json(silent=True)

    print("WhatsApp webhook received:")
    print(data)

    try:

        if not data:
            return "OK", 200

        if data.get("object") != "whatsapp_business_account":
            return "OK", 200

        for entry in data.get("entry", []):

            for change in entry.get("changes", []):

                value = change.get("value", {})

                messages = value.get("messages", [])

                for message in messages:

                    process_whatsapp_message(message)

    except Exception as e:

        print("WhatsApp webhook error:", e)

    return "EVENT_RECEIVED", 200


# =========================================================
# PROCESS WHATSAPP MESSAGE
# =========================================================

def process_whatsapp_message(message):

    phone = message.get("from")

    if not phone:
        return

    message_type = message.get("type")

    print(
        f"WhatsApp message from {phone}: "
        f"type={message_type}"
    )

    # ---------------------------------------------
    # TEXT MESSAGE
    # ---------------------------------------------

    if message_type == "text":

        text = message.get("text", {}).get("body", "").strip()

        handle_whatsapp_text(phone, text)

    # ---------------------------------------------
    # IMAGE
    # ---------------------------------------------

    elif message_type == "image":

        media_id = message.get("image", {}).get("id")

        handle_whatsapp_cv(
            phone,
            media_id,
            "image"
        )

    # ---------------------------------------------
    # DOCUMENT
    # ---------------------------------------------

    elif message_type == "document":

        media_id = message.get("document", {}).get("id")

        filename = message.get("document", {}).get(
            "filename",
            "CV"
        )

        handle_whatsapp_cv(
            phone,
            media_id,
            "document",
            filename
        )

    else:

        send_whatsapp_message(
            phone,
            "Please send a text message, CV document or photo."
        )


# =========================================================
# WHATSAPP TEXT HANDLER
# =========================================================

def handle_whatsapp_text(phone, text):

    text_lower = text.lower()

    # ---------------------------------------------
    # NEW USER / MENU
    # ---------------------------------------------

    if text_lower in [
        "hi",
        "hello",
        "hey",
        "start",
        "menu",
        "jobs",
        "job"
    ]:

        whatsapp_users[phone] = {
            "step": "menu"
        }

        send_whatsapp_message(
            phone,
            "Welcome to Husaraaj Recruitment Agency!\n\n"
            "Your trusted partner for jobs abroad.\n\n"
            "Reply with:\n\n"
            "1. JOBS AVAILABLE\n"
            "2. CONTACT US"
        )

        return

    # ---------------------------------------------
    # MAIN MENU
    # ---------------------------------------------

    user = whatsapp_users.get(phone, {})

    step = user.get("step")

    if step == "menu":

        if text_lower in ["1", "jobs", "jobs available"]:

            user["step"] = "country"

            send_whatsapp_message(
                phone,
                "Select Country:\n\n"
                "1. 🇶🇦 Qatar\n"
                "2. 🇸🇦 Saudi Arabia\n"
                "3. 🇦🇪 Dubai / UAE"
            )

            return

        elif text_lower in ["2", "contact", "contact us"]:

            send_whatsapp_message(
                phone,
                "📞 Contact Husaraaj:\n"
                "+256 730465869\n\n"
                "Location: Kampala, Uganda"
            )

            return

    # ---------------------------------------------
    # COUNTRY
    # ---------------------------------------------

    if step == "country":

        country = None

        if text_lower in ["1", "qatar"]:
            country = "QATAR"

        elif text_lower in ["2", "saudi", "saudi arabia"]:
            country = "SAUDI"

        elif text_lower in [
            "3",
            "dubai",
            "uae",
            "united arab emirates"
        ]:
            country = "DUBAI"

        if country:

            user["country"] = country
            user["step"] = "apply"

            send_whatsapp_message(
                phone,
                f"Jobs available in {country}:\n\n"
                "- House Maid\n"
                "- Driver\n"
                "- Cleaner\n"
                "- Security\n\n"
                "Reply APPLY to start your application."
            )

            return

    # ---------------------------------------------
    # START APPLICATION
    # ---------------------------------------------

    if step == "apply":

        if text_lower == "apply":

            user["step"] = "name"

            send_whatsapp_message(
                phone,
                "Great! Let's start your application.\n\n"
                "What is your FULL NAME?"
            )

            return

    # ---------------------------------------------
    # NAME
    # ---------------------------------------------

    if step == "name":

        user["name"] = text
        user["step"] = "age"

        send_whatsapp_message(
            phone,
            "How old are you? (Enter Age)"
        )

        return

    # ---------------------------------------------
    # AGE
    # ---------------------------------------------

    if step == "age":

        user["age"] = text
        user["step"] = "phone"

        send_whatsapp_message(
            phone,
            "What is your Phone Number?"
        )

        return

    # ---------------------------------------------
    # PHONE
    # ---------------------------------------------

    if step == "phone":

        user["phone"] = text
        user["step"] = "location"

        send_whatsapp_message(
            phone,
            "Where do you live? (District)"
        )

        return

    # ---------------------------------------------
    # LOCATION
    # ---------------------------------------------

    if step == "location":

        user["location"] = text
        user["step"] = "passport"

        send_whatsapp_message(
            phone,
            "Do you have a Passport?\n\n"
            "Reply YES or NO."
        )

        return

    # ---------------------------------------------
    # PASSPORT
    # ---------------------------------------------

    if step == "passport":

        if text_lower in ["yes", "y"]:
            user["passport"] = "Yes"

        elif text_lower in ["no", "n"]:
            user["passport"] = "No"

        else:

            send_whatsapp_message(
                phone,
                "Please reply YES or NO."
            )

            return

        user["step"] = "experience"

        send_whatsapp_message(
            phone,
            "Do you have experience abroad?\n\n"
            "Reply YES or NO."
        )

        return

    # ---------------------------------------------
    # EXPERIENCE
    # ---------------------------------------------

    if step == "experience":

        if text_lower in ["yes", "y"]:
            user["experience"] = "Yes"

        elif text_lower in ["no", "n"]:
            user["experience"] = "No"

        else:

            send_whatsapp_message(
                phone,
                "Please reply YES or NO."
            )

            return

        user["step"] = "cv"

        send_whatsapp_message(
            phone,
            "Last step:\n\n"
            "Please send your CV, photo, "
            "or write about yourself."
        )

        return

    # ---------------------------------------------
    # CV AS TEXT
    # ---------------------------------------------

    if step == "cv":

        user["cv_text"] = text

        send_whatsapp_application_to_admin(
            phone,
            user
        )

        send_whatsapp_message(
            phone,
            "✅ Application Received!\n\n"
            "Husaraaj team will contact you soon.\n"
            "Thank you!"
        )

        whatsapp_users.pop(phone, None)

        return

    # ---------------------------------------------
    # DEFAULT
    # ---------------------------------------------

    send_whatsapp_message(
        phone,
        "Welcome to Husaraaj Recruitment Agency.\n\n"
        "Reply JOBS to see available jobs."
    )


# =========================================================
# WHATSAPP CV / PHOTO
# =========================================================

def handle_whatsapp_cv(
    phone,
    media_id,
    media_type,
    filename="CV"
):

    user = whatsapp_users.get(phone)

    if not user:

        send_whatsapp_message(
            phone,
            "Please first type JOBS to start your application."
        )

        return

    if user.get("step") != "cv":

        send_whatsapp_message(
            phone,
            "Please complete the application questions first."
        )

        return

    user["cv_media_id"] = media_id
    user["cv_media_type"] = media_type
    user["cv_filename"] = filename

    send_whatsapp_application_to_admin(
        phone,
        user
    )

    # Try to send CV/photo to admin
    send_whatsapp_media_to_admin(
        media_id,
        media_type,
        filename
    )

    send_whatsapp_message(
        phone,
        "✅ Application Received!\n\n"
        "Your CV/photo has been received.\n"
        "Husaraaj team will contact you soon.\n"
        "Thank you!"
    )

    whatsapp_users.pop(phone, None)


# =========================================================
# SEND APPLICATION TO WHATSAPP ADMIN
# =========================================================

def send_whatsapp_application_to_admin(
    applicant_phone,
    data
):

    admin_text = (
        "🔥 NEW WHATSAPP APPLICATION 🔥\n\n"
        f"Country: {data.get('country')}\n"
        f"Name: {data.get('name')}\n"
        f"Age: {data.get('age')}\n"
        f"Phone: {data.get('phone')}\n"
        f"Location: {data.get('location')}\n"
        f"Passport: {data.get('passport')}\n"
        f"Experience: {data.get('experience')}\n"
        f"WhatsApp: +{applicant_phone}\n"
        f"Time: {datetime.datetime.now()}\n"
    )

    cv_text = data.get("cv_text")

    if cv_text:
        admin_text += (
            "\nCV / About Applicant:\n"
            f"{cv_text}"
        )

    send_whatsapp_message(
        WHATSAPP_ADMIN_NUMBER,
        admin_text
    )


# =========================================================
# DOWNLOAD WHATSAPP MEDIA
# =========================================================

def get_whatsapp_media_url(media_id):

    headers = {
        "Authorization":
            f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }

    url = (
        f"https://graph.facebook.com/"
        f"{WHATSAPP_API_VERSION}/"
        f"{media_id}"
    )

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        print(
            "Media information:",
            response.status_code,
            response.text
        )

        if response.ok:

            return response.json().get("url")

    except Exception as e:

        print("Media URL error:", e)

    return None


# =========================================================
# SEND CV / PHOTO TO ADMIN
# =========================================================

def send_whatsapp_media_to_admin(
    media_id,
    media_type,
    filename="CV"
):

    media_url = get_whatsapp_media_url(media_id)

    if not media_url:
        print("Could not get WhatsApp media URL.")
        return

    headers = {
        "Authorization":
            f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }

    try:

        response = requests.get(
            media_url,
            headers=headers,
            timeout=60
        )

        if not response.ok:

            print(
                "Could not download media:",
                response.text
            )

            return

        # Upload media to WhatsApp
        files = {
            "file": (
                filename,
                response.content
            )
        }

        upload_data = {
            "messaging_product": "whatsapp"
        }

        upload_url = (
            f"https://graph.facebook.com/"
            f"{WHATSAPP_API_VERSION}/"
            f"{WHATSAPP_PHONE_NUMBER_ID}/media"
        )

        upload_response = requests.post(
            upload_url,
            headers={
                "Authorization":
                    f"Bearer {WHATSAPP_ACCESS_TOKEN}"
            },
            data=upload_data,
            files=files,
            timeout=60
        )

        print(
            "Media upload:",
            upload_response.status_code,
            upload_response.text
        )

        if not upload_response.ok:
            return

        new_media_id = upload_response.json().get("id")

        if not new_media_id:
            return

        # -----------------------------------------
        # SEND IMAGE
        # -----------------------------------------

        if media_type == "image":

            payload = {
                "messaging_product": "whatsapp",
                "to": WHATSAPP_ADMIN_NUMBER,
                "type": "image",
                "image": {
                    "id": new_media_id
                }
            }

        # -----------------------------------------
        # SEND DOCUMENT
        # -----------------------------------------

        else:

            payload = {
                "messaging_product": "whatsapp",
                "to": WHATSAPP_ADMIN_NUMBER,
                "type": "document",
                "document": {
                    "id": new_media_id,
                    "filename": filename
                }
            }

        send_response = requests.post(
            whatsapp_url(),
            headers={
                "Authorization":
                    f"Bearer {WHATSAPP_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )

        print(
            "Media sent to admin:",
            send_response.status_code,
            send_response.text
        )

    except Exception as e:

        print(
            "Error sending WhatsApp media:",
            e
        )


# =========================================================
# START FLASK
# =========================================================

def run_web_server():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    web_app.run(
        host="0.0.0.0",
        port=port
    )


# =========================================================
# TELEGRAM CONFIG
# =========================================================

TOKEN = os.getenv(
    "BOT_TOKEN",
    "8714999222:AAHJiSHubcMiinZRfzNmGFggiDGmVIS5GmQ"
)

ADMIN_ID = 1456630398


# Conversation states
NAME, AGE, PHONE, LOCATION, PASSPORT, EXPERIENCE, CV = range(7)


# =========================================================
# TELEGRAM START MENU
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        f"New Telegram user: "
        f"{update.effective_user.first_name} "
        f"ID: {update.effective_user.id}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "💼 JOBS AVAILABLE",
                callback_data="jobs_list"
            )
        ],
        [
            InlineKeyboardButton(
                "📞 CONTACT US",
                callback_data="contact"
            )
        ],
    ]

    text = (
        "Welcome to Husaraaj Recruitment Agency!\n\n"
        "Your trusted partner for jobs abroad.\n\n"
        "Choose an option:"
    )

    if update.message:

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

    else:

        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )


# =========================================================
# TELEGRAM MENU
# =========================================================

async def handle_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.data == "jobs_list":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🇶🇦 QATAR Jobs",
                    callback_data="jobs_qatar"
                )
            ],
            [
                InlineKeyboardButton(
                    "🇸🇦 SAUDI Jobs",
                    callback_data="jobs_saudi"
                )
            ],
            [
                InlineKeyboardButton(
                    "🇦🇪 DUBAI Jobs",
                    callback_data="jobs_dubai"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="back_menu"
                )
            ],
        ]

        await query.message.edit_text(
            "Select Country:",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

    elif query.data.startswith("jobs_"):

        country = (
            query.data
            .split("_")[1]
            .upper()
        )

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
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

    elif query.data.startswith("apply_"):

        context.user_data["country"] = (
            query.data.split("_")[1]
        )

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
            "+256 730465869\n"
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
# TELEGRAM APPLICATION
# =========================================================

async def get_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["name"] = update.message.text

    await update.message.reply_text(
        "How old are you? (Enter Age)"
    )

    return AGE


async def get_age(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["age"] = update.message.text

    await update.message.reply_text(
        "What is your Phone Number?"
    )

    return PHONE


async def get_phone(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["phone"] = update.message.text

    await update.message.reply_text(
        "Where do you live? (District)"
    )

    return LOCATION


async def get_location(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )

    return PASSPORT


async def get_passport(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    context.user_data["passport"] = (
        query.data.split("_")[1]
    )

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
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )

    return EXPERIENCE


async def get_experience(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    context.user_data["experience"] = (
        query.data.split("_")[1]
    )

    await query.message.edit_text(
        "Last step: Send your CV / Photo / "
        "or write about yourself"
    )

    return CV


async def get_cv(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    data = context.user_data

    admin_text = (
        "🔥 NEW TELEGRAM APPLICATION 🔥\n\n"
        f"Country: {data.get('country')}\n"
        f"Name: {data.get('name')}\n"
        f"Age: {data.get('age')}\n"
        f"Phone: {data.get('phone')}\n"
        f"Location: {data.get('location')}\n"
        f"Passport: {data.get('passport')}\n"
        f"Experience: {data.get('experience')}\n\n"
        f"From: {user.first_name} "
        f"ID: {user.id}\n"
        f"Time: {datetime.datetime.now()}"
    )

    try:

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
        )

        if (
            update.message.document
            or update.message.photo
        ):

            await context.bot.forward_message(
                chat_id=ADMIN_ID,
                from_chat_id=(
                    update.effective_chat.id
                ),
                message_id=(
                    update.message.message_id
                ),
            )

        elif update.message.text:

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"CV Text: "
                    f"{update.message.text}"
                ),
            )

    except Exception as e:

        print(
            f"Failed to send to Telegram admin: {e}"
        )

    await update.message.reply_text(
        "✅ Application Received!\n\n"
        "Husaraaj team will contact you soon. "
        "Thank you!"
    )

    await start(update, context)

    return ConversationHandler.END


# =========================================================
# TELEGRAM CANCEL
# =========================================================

async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "Cancelled. Type /start to begin again."
    )

    return ConversationHandler.END


# =========================================================
# MAIN
# =========================================================

def main():

    # Start Flask
    threading.Thread(
        target=run_web_server,
        daemon=True,
    ).start()

    # Telegram connection
    request_config = HTTPXRequest(
        connection_pool_size=20,
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0,
    )

    app = (
        Application.builder()
        .token(TOKEN)
        .request(request_config)
        .build()
    )

    # Telegram conversation
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
                    filters.TEXT
                    & ~filters.COMMAND,
                    get_name,
                )
            ],

            AGE: [
                MessageHandler(
                    filters.TEXT
                    & ~filters.COMMAND,
                    get_age,
                )
            ],

            PHONE: [
                MessageHandler(
                    filters.TEXT
                    & ~filters.COMMAND,
                    get_phone,
                )
            ],

            LOCATION: [
                MessageHandler(
                    filters.TEXT
                    & ~filters.COMMAND,
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

    # Telegram commands
    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    # Telegram menu
    app.add_handler(
        CallbackQueryHandler(
            handle_menu,
            pattern="^(jobs_|back_menu|contact)",
        )
    )

    # Telegram application
    app.add_handler(conv_handler)

    print("====================================")
    print("HUSARAAJ BOT IS RUNNING")
    print("====================================")
    print("Telegram bot connected.")
    print("WhatsApp webhook ready.")
    print("Flask web server running.")

    # Start Telegram
    app.run_polling()


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()
