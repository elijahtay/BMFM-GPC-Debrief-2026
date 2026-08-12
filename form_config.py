"""
Configuration describing the Google Form this bot submits to.

This file was generated for:
  Form title: "BMFM GPC 2026 Feedback"
  Form URL:   https://docs.google.com/forms/d/e/1FAIpQLSeqyNB9BR5hIuCJaipbQXRzvQd3jv0mEK7upoS44W4nD-yW9A/viewform

If the Google Form's questions ever change (new question added/removed, or
wording changed enough that you rebuild the form), re-run
`get_form_fields.py <form-url>` to regenerate the ENTRY IDs below, then update
FORM_QUESTIONS to match.

Each question is a dict with:
  key         - internal identifier (used in the code, not shown to users)
  entry_id    - the Google Form field id ("entry.XXXXXXXXX")
  prompt      - the message text sent to the Telegram user
  type        - "text" | "choice"
  options     - list of button labels (only for type == "choice"); the exact
                text sent to Google must match the option text in the form
  required    - whether the bot should insist on a non-empty answer
                (independent of whether the Google Form itself marks it
                required - none of the fields in this form are required on
                the Google side, but we still ask for all of them)
"""

FORM_ID = "1FAIpQLSeqyNB9BR5hIuCJaipbQXRzvQd3jv0mEK7upoS44W4nD-yW9A"
FORM_RESPONSE_URL = f"https://docs.google.com/forms/d/e/{FORM_ID}/formResponse"
FORM_VIEW_URL = f"https://docs.google.com/forms/d/e/{FORM_ID}/viewform"

FORM_TITLE = "BMFM GPC 2026 Feedback"
FORM_DESCRIPTION = (
    "Please share your insights on what we should start, stop, or keep for "
    "next year GPC. You may submit this form multiple times for different items."
)

FORM_QUESTIONS = [
    {
        "key": "full_name",
        "entry_id": "entry.1160596783",
        "prompt": "What's your full name? (Send /skip to leave this blank)",
        "type": "text",
        "required": False,
    },
    {
        "key": "category",
        "entry_id": "entry.1718701687",
        "prompt": "Which category does your feedback fall under?",
        "type": "choice",
        "options": [
            "Start (New initiatives we should implement)",
            "Stop (Activities that are no longer effective)",
            "Keep (Successful elements we should maintain)",
        ],
        "required": True,
    },
    {
        "key": "detail",
        "entry_id": "entry.22757714",
        "prompt": "Please provide the specific detail or activity for your feedback.",
        "type": "text",
        "required": True,
    },
    {
        "key": "reason",
        "entry_id": "entry.1132835721",
        "prompt": "Why do you feel this should be started, stopped, or kept?",
        "type": "text",
        "required": True,
    },
]
