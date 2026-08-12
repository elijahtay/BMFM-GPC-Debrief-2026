# Telegram → Google Form bot

A Telegram bot that asks users the same questions as your Google Form
("BMFM GPC 2026 Feedback"), then submits their answers straight into the
form — so Telegram responses land in the same consolidated spreadsheet as
everyone else's.

## How it works

Google Forms accept plain POST requests at a `.../formResponse` URL, the
same endpoint the form itself uses behind the scenes. Each question has a
hidden `entry.XXXXXXXXX` field ID. The bot:

1. Asks the user each question one at a time, in a Telegram chat.
2. Uses the matching field type (free text or button choices) for each
   question, defined in `form_config.py`.
3. Shows a summary and asks for confirmation.
4. On confirm, POSTs the answers to the form's `formResponse` URL using the
   correct `entry.*` field IDs — Google records it exactly as if the user
   had filled in the form themselves.

No Google API credentials or OAuth are needed, because this uses the form's
public submission endpoint (the same one your web browser uses).

## Files

- `bot.py` — the bot itself.
- `form_config.py` — the question text, field types, and Google Form entry
  IDs. Edit this if you change the wording of your bot prompts, or
  regenerate it if the underlying Google Form changes.
- `get_form_fields.py` — a standalone helper to inspect any public Google
  Form and print its questions/entry IDs. Run this again if you add,
  remove, or change questions on the Google Form.
- `requirements.txt` — Python dependencies.
- `.env.example` — template for your bot token.
- `Procfile` — tells hosting platforms like Railway how to start the bot.

## Setup

1. **Install dependencies** (Python 3.10+ recommended):

   ```bash
   pip install -r requirements.txt
   ```

2. **Add your bot token.** Copy `.env.example` to `.env`:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` and paste in the token you got from
   [@BotFather](https://t.me/BotFather):

   ```
   TELEGRAM_BOT_TOKEN=123456789:AAour-real-token-here
   ```

   Keep this file private — never commit it or paste the token into a chat.

3. **Run the bot:**

   ```bash
   python bot.py
   ```

   You should see `Bot starting (polling)...` in the console. Open your bot
   in Telegram and send `/start`.

## Commands

- `/start` — begin (or restart) a feedback submission.
- `/skip` — skip the current question, if it isn't required (only "Full
  Name" is skippable in this form).
- `/cancel` — abandon the current submission without sending anything.

Because the Google Form itself allows multiple submissions per person,
users can run `/start` again to submit feedback on another item.

## Keeping it in sync with the Google Form

If you edit the questions on the Google Form later (reword a question, add
a new one, change multiple-choice options), the bot's copy in
`form_config.py` won't update automatically. To regenerate it:

```bash
python get_form_fields.py "https://docs.google.com/forms/d/e/<FORM_ID>/viewform"
```

This prints each question's type, entry ID, and options. Update
`FORM_QUESTIONS` in `form_config.py` to match, and add/remove a matching
entry if you added/removed a question (each dict needs `key`, `entry_id`,
`prompt`, `type`, and `required`; add `options` for choice-type questions).

## Deploying so it runs continuously

Running `python bot.py` on your laptop only works while your laptop is on
and connected. For a bot people can use any time, run it somewhere that
stays online:

- **A small always-on server / Raspberry Pi**: run it under `systemd` or
  `pm2` so it restarts automatically if it crashes or the machine reboots.
- **Railway**: see the dedicated section below.
- **Other low-cost platforms** (Render, Fly.io): push this folder as a
  repo, set `TELEGRAM_BOT_TOKEN` as an environment variable in the
  platform's dashboard (instead of a `.env` file), and set the start
  command to `python bot.py`.
- **Google Cloud Run / a serverless platform**: this would require
  switching from polling (`run_polling`) to a webhook — ask if you'd like
  a webhook-based version instead; it's a fairly small change.

Wherever you host it, treat the bot token like a password: set it as an
environment variable / secret in that platform rather than hardcoding it
in the code.

### Deploying on Railway

1. Push this folder to a GitHub repo (or use Railway's CLI to deploy the
   folder directly) — but don't commit your real `.env` file. Add a
   `.gitignore` with `.env` in it if you haven't already.
2. In Railway, create a new service from that repo.
3. Go to the service's **Variables** tab and add `TELEGRAM_BOT_TOKEN` with
   your real token. Railway injects it as an environment variable, so
   `os.environ.get("TELEGRAM_BOT_TOKEN")` in `bot.py` picks it up
   automatically — no `.env` file needed on Railway.
4. Railway should auto-detect the `Procfile` included here (`worker:
   python bot.py`) and use it as the start command. If it doesn't, set the
   **Start Command** manually in the service's Settings tab to
   `python bot.py`.
5. Leave **public networking / a domain disabled** for this service. The
   bot uses polling, not a webhook, so it never listens on an HTTP port —
   if Railway tries to health-check it as a web service, it may get killed
   for "failing" a check it was never meant to pass.
6. Deploy. Check the **Deployments → Logs** tab for `Bot starting
   (polling)...` to confirm it's running.

A couple of Railway-specific things worth knowing:

- **Every redeploy restarts the process**, which clears the bot's
  in-memory conversation state. Anyone mid-conversation at that moment will
  need to send `/start` again — not a bug, just how in-memory state and
  redeploys interact.
- **Billing**: this is a long-running process (polling never stops), so
  Railway bills it for continuous uptime rather than per-request. Fine for
  a low-traffic internal tool, but worth checking your plan/usage if cost
  matters.

## Notes on the data

This form and bot only collect an optional name plus general programme
feedback (start/stop/keep) — nothing from HOGC's Confidential or Highly
Confidential categories (no pastoral, medical, financial, disciplinary, or
minors' data). If you ever reuse this bot for a form that *does* collect
that kind of information, check with the AI Governance and Security Team
first and anonymise responses before any AI-assisted analysis of them.
