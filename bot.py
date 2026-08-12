#!/usr/bin/env python3
"""
Telegram bot that collects answers conversationally and submits them to the
"BMFM GPC 2026 Feedback" Google Form, so responses from Telegram land in the
same consolidated spreadsheet as everyone else's form submissions.

Setup:
    1. pip install -r requirements.txt
    2. Copy .env.example to .env and fill in TELEGRAM_BOT_TOKEN
    3. python bot.py

See README.md for full setup and deployment instructions.
"""

import logging
import os

import httpx
from dotenv import load_dotenv
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from form_config import FORM_DESCRIPTION, FORM_QUESTIONS, FORM_RESPONSE_URL, FORM_TITLE

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Each question in FORM_QUESTIONS becomes one conversation state, in order,
# followed by a final CONFIRM state.
QUESTION_STATES = range(len(FORM_QUESTIONS))
CONFIRM = len(FORM_QUESTIONS)

ANSWERS_KEY = "answers"  # key used in context.user_data to stash answers


def _question(index: int) -> dict:
    return FORM_QUESTIONS[index]


def _build_keyboard(index: int):
    q = _question(index)
    if q["type"] == "choice":
        return ReplyKeyboardMarkup(
            [[opt] for opt in q["options"]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
    return ReplyKeyboardRemove()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[ANSWERS_KEY] = {}
    await update.message.reply_text(
        f"👋 {FORM_TITLE}\n\n{FORM_DESCRIPTION}\n\n"
        "I'll ask you a few quick questions and submit your response for you.\n"
        "Send /cancel any time to stop.",
    )
    return await _ask(update, context, 0)


async def _ask(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int) -> int:
    context.user_data["_current_index"] = index
    q = _question(index)
    await update.message.reply_text(q["prompt"], reply_markup=_build_keyboard(index))
    return index


def _make_answer_handler(index: int):
    """Build the handler for question `index` that stores the answer and
    advances to the next question (or to confirmation)."""

    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        q = _question(index)
        text = update.message.text.strip()

        if q["type"] == "choice" and text not in q["options"]:
            await update.message.reply_text(
                "Please choose one of the options using the buttons below.",
                reply_markup=_build_keyboard(index),
            )
            return index

        if q["required"] and not text:
            await update.message.reply_text("This one can't be left blank - please answer:")
            return index

        context.user_data[ANSWERS_KEY][q["key"]] = text

        next_index = index + 1
        if next_index < len(FORM_QUESTIONS):
            return await _ask(update, context, next_index)
        return await _show_summary(update, context)

    return handler


async def skip_current(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles /skip - only meant to be used on non-required questions."""
    # Figure out which state we're in from the conversation handler isn't
    # directly exposed here, so we track it via user_data instead.
    index = context.user_data.get("_current_index", 0)
    q = _question(index)
    if q["required"]:
        await update.message.reply_text("Sorry, this question can't be skipped.")
        return index
    context.user_data[ANSWERS_KEY][q["key"]] = ""
    next_index = index + 1
    if next_index < len(FORM_QUESTIONS):
        return await _ask(update, context, next_index)
    return await _show_summary(update, context)


async def _show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answers = context.user_data[ANSWERS_KEY]
    lines = ["Here's what I've got:\n"]
    for q in FORM_QUESTIONS:
        value = answers.get(q["key"]) or "(blank)"
        lines.append(f"• {q['prompt']}\n  → {value}")
    lines.append("\nSubmit this to the form?")

    keyboard = ReplyKeyboardMarkup(
        [["✅ Submit"], ["❌ Cancel"]], resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text("\n".join(lines), reply_markup=keyboard)
    return CONFIRM


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().lower()
    if "submit" in text:
        answers = context.user_data[ANSWERS_KEY]
        payload = {
            q["entry_id"]: answers.get(q["key"], "") for q in FORM_QUESTIONS
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(FORM_RESPONSE_URL, data=payload)
            if resp.status_code == 200:
                await update.message.reply_text(
                    "✅ Thanks! Your response has been submitted.\n\n"
                    "Send /start to submit another response.",
                    reply_markup=ReplyKeyboardRemove(),
                )
            else:
                logger.warning("Form submission returned status %s", resp.status_code)
                await update.message.reply_text(
                    "⚠️ Something went wrong submitting your response "
                    f"(status {resp.status_code}). Please try again with /start, "
                    "or let the organiser know if this keeps happening.",
                    reply_markup=ReplyKeyboardRemove(),
                )
        except httpx.HTTPError as exc:
            logger.exception("Error submitting to Google Form")
            await update.message.reply_text(
                "⚠️ I couldn't reach the form right now. Please try again in a "
                "moment with /start.",
                reply_markup=ReplyKeyboardRemove(),
            )
        context.user_data.clear()
        return ConversationHandler.END

    await update.message.reply_text(
        "No problem, I've discarded that response. Send /start to begin again.",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Cancelled. Send /start whenever you'd like to submit feedback.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def build_application() -> Application:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. Copy .env.example to .env and fill it in."
        )

    application = Application.builder().token(token).build()

    states = {}
    for i in range(len(FORM_QUESTIONS)):
        states[i] = [
            CommandHandler("skip", skip_current),
            MessageHandler(filters.TEXT & ~filters.COMMAND, _make_answer_handler(i)),
        ]
    states[CONFIRM] = [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)]

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states=states,
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    return application


def main():
    application = build_application()
    logger.info("Bot starting (polling)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
