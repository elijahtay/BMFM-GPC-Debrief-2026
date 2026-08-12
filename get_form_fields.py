#!/usr/bin/env python3
"""
Utility to inspect any public Google Form and print out its questions,
field types, and entry IDs - the same information that was used to build
form_config.py.

Use this whenever the linked Google Form's questions change, or if you want
to point this bot (or a copy of it) at a different form.

Usage:
    python get_form_fields.py "https://docs.google.com/forms/d/e/<FORM_ID>/viewform"

This only reads the form's public HTML - it does not require any Google
API credentials, and it does not submit anything.
"""

import json
import re
import sys

import httpx

TYPE_MAP = {
    0: "SHORT_TEXT",
    1: "PARAGRAPH",
    2: "MULTIPLE_CHOICE",
    3: "DROPDOWN",
    4: "CHECKBOXES",
    5: "LINEAR_SCALE",
    7: "GRID",
    9: "DATE",
    10: "TIME",
}


def fetch_form_data(form_url: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; FormFieldInspector/1.0)"}
    resp = httpx.get(form_url, headers=headers, follow_redirects=True, timeout=30)
    resp.raise_for_status()
    match = re.search(r"FB_PUBLIC_LOAD_DATA_ = (.*?);</script>", resp.text, re.S)
    if not match:
        raise RuntimeError(
            "Could not find form data on the page. Make sure the form is "
            "public ('Anyone with the link can respond') and the URL is a "
            "viewform link."
        )
    return json.loads(match.group(1))


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    form_url = sys.argv[1]
    data = fetch_form_data(form_url)

    title = data[3] if len(data) > 3 else None
    description = data[0] if isinstance(data[0], str) else None
    print(f"Form title: {title}")
    print(f"Description: {description}")
    print()

    questions = data[1][1] if data[1] else []
    for q in questions:
        qid, title, help_text, qtype = q[0], q[1], q[2], q[3]
        entries = q[4] or []
        print(f"--- {TYPE_MAP.get(qtype, f'TYPE_{qtype}')} ---")
        print(f"Question: {title}")
        if help_text:
            print(f"Help text: {help_text}")
        for e in entries:
            entry_id, options, required = e[0], e[1], (e[2] if len(e) > 2 else None)
            print(f"  entry_id: entry.{entry_id}   required={bool(required)}")
            if options:
                print("  options:")
                for opt in options:
                    print(f"    - {opt[0]}")
        print()


if __name__ == "__main__":
    main()
