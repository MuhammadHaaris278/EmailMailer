import os
import smtplib
import json
import imaplib
import email
import re
import requests
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL = "codellama"
EMAIL_REGEX = r"[^@]+@[^@]+\.[^@]+"

# --- Email Sending ---
def send_email(recipient, subject, body):
    EMAIL_ADDRESS = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASS")

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise ValueError("Missing email credentials.")

    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"\n✅ Email sent successfully to {recipient}.")
    except Exception as e:
        print(f"\n❌ Failed to send email: {str(e)}")

# --- Email Fetching ---
def get_latest_email_body():
    EMAIL_ADDRESS = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASS")
    IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
    IMAP_PORT = int(os.getenv("IMAP_PORT", 993))

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select("inbox")
        _, search_data = mail.search(None, 'UNSEEN')
        email_ids = search_data[0].split()

        if not email_ids:
            return "No unread emails found."

        latest_id = email_ids[-1]
        _, msg_data = mail.fetch(latest_id, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode("utf-8")

        return "Couldn't extract email body."
    except Exception as e:
        return f"❌ Failed to fetch email: {str(e)}"

# --- LLaMA Prompt ---
def llama_prompt(prompt: str):
    res = requests.post(OLLAMA_API_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })
    return res.json()["response"].strip()

# --- Email Fallback Subject/Body Generator ---
def complete_email_fields(recipient, message_intent):
    prompt = f"""
You are an AI email assistant. Generate a well-written, detailed, emotionally resonant email based on the user's intent. The subject should be relevant and attention-grabbing. The body must be long, expressive, grammatically correct, and should not repeat lines.

Email recipient: {recipient}
User intent: {message_intent}

Return only valid JSON with the keys "subject" and "body":
{{
  "subject": "Subject goes here",
  "body": "Full email content here, with paragraphs."
}}
"""
    try:
        raw = llama_prompt(prompt)
        parsed = json.loads(raw.strip() if '```' not in raw else raw.split('```json')[-1].split('```')[0])
        return parsed.get("subject", ""), parsed.get("body", "")
    except:
        return "", ""

# --- Validation ---
def is_valid_email_args(args):
    return (
        re.match(EMAIL_REGEX, args.get("recipient", "")) and
        args.get("subject") and
        args.get("body") and
        "[Your Name]" not in args["body"]
    )

# --- Prompt Instruction ---
instruction = """
You are a strict assistant that only handles two tasks:
1. Sending an email
2. Summarizing the latest unread email

User instructions will be in natural language.

Respond ONLY with JSON:
- If unrelated: {"function": "none"}
- If summarizing latest email: {"function": "summarize_latest_email"}
- If sending email (with recipient, subject, body): 
  {
    "function": "send_email",
    "args": {
      "recipient": "EMAIL_HERE",
      "subject": "SUBJECT_HERE",
      "body": "BODY_HERE"
    }
  }
- If fields are missing: 
  {
    "function": "ask_missing_info",
    "missing": ["recipient", "subject", "body"]
  }

NEVER invent info. NEVER return anything other than the required JSON.
"""

# --- Main Loop ---
if __name__ == "__main__":
    while True:
        user_input = input("\n💬 What would you like to do?\n\n-> ").strip().lower()

        if user_input in ["quit", "exit", "q"]:
            print("\n👋 Goodbye!")
            break

        full_prompt = instruction + "\n\nUser: " + user_input

        try:
            raw = llama_prompt(full_prompt)

            if '```' in raw:
                raw_json = raw.split('```json')[-1].split('```')[0]
            else:
                raw_json = raw

            parsed = json.loads(raw_json.strip())
            func = parsed.get("function", "none")

            if func == "send_email":
                args = parsed.get("args", {})
                if not is_valid_email_args(args):
                    print("⚠️ LLaMA response incomplete. Attempting to regenerate subject/body...")

                    recipient = args.get("recipient", "")
                    prompt_as_intent = user_input.replace(recipient, "").strip()

                    subject, body = complete_email_fields(recipient, prompt_as_intent)

                    if not re.match(EMAIL_REGEX, recipient) or not subject or not body:
                        print("❌ Still couldn't generate a valid email. Please try again.")
                        continue

                    print(f"\n📧 Ready to send the following email:")
                    print(f"To: {recipient}")
                    print(f"Subject: {subject}")
                    print(f"Body:\n{body}\n")

                    confirm = input("Send this email? (y/n): ").strip().lower()
                    if confirm != 'y':
                        print("❌ Cancelled.")
                        continue

                    send_email(recipient, subject, body)
                else:
                    send_email(**args)

            elif func == "summarize_latest_email":
                email_body = get_latest_email_body()
                if email_body.startswith("❌"):
                    print(email_body)
                    continue
                summary = llama_prompt(f"Summarize this email:\n\n{email_body}")
                print("\n📬 Email Summary:\n", summary)

            elif func == "ask_missing_info":
                missing = parsed.get("missing", [])
                completed_args = {}

                for field in missing:
                    value = input(f"Enter {field}: ").strip()
                    completed_args[field] = value

                if is_valid_email_args(completed_args):
                    send_email(**completed_args)
                else:
                    print("❌ Provided values were not valid for email sending.")

            else:
                print("\n⚠️ Sorry, I can only *send an email* or *summarize your latest email*.")

        except Exception as e:
            print("\n❌ Something went wrong.")
            print("Reason:", str(e))
