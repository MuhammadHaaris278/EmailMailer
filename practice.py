import os
import smtplib
import json
import imaplib
import email
from email.message import EmailMessage
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Setup OpenAI Client (GitHub GPT-4.1)
client = OpenAI(
    base_url="https://models.github.ai/inference",
    api_key=os.getenv("GITHUB_TOKEN"),
)
model = "openai/gpt-4.1"

# Define Functions


def send_email(recipient, subject, body):
    EMAIL_ADDRESS = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASS")

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise ValueError("Missing email credentials in environment variables.")

    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
        print("Email sent successfully.")


def get_latest_email_body():
    EMAIL_ADDRESS = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASS")
    IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
    IMAP_PORT = int(os.getenv("IMAP_PORT", 993))

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


# Tool/Function definitions
function_definitions = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email with subject, recipient, and body",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["recipient", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_latest_email",
            "description": "Fetch and summarize the latest unread email from your inbox.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

# Main chatbot loop
while True:
    user_prompt = input("\n💬 What would you like to do? \n\n-> ").strip()

    # Step 1: Classify Intent
    intent_check = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an intent classifier. "
                    "Only respond with one of the following: 'send_email', 'summarize_latest_email', or 'none'."
                )
            },
            {"role": "user", "content": user_prompt}
        ]
    )
    intent = intent_check.choices[0].message.content.strip().lower()

    if intent not in ["send_email", "summarize_latest_email"]:
        print("\nSorry, I cannot help you with that.")
        print("I am here to either *Send an email* or *Summarize the latest one in your inbox.*")
        continue

    # Step 2: Let GPT attempt tool calling
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You can only assist with sending emails or summarizing the latest email. Use the appropriate tool functions only."
            },
            {"role": "user", "content": user_prompt}
        ],
        tools=function_definitions,
        tool_choice="auto",
    )

    choice_msg = response.choices[0].message

    if choice_msg.tool_calls:
        tool_call = choice_msg.tool_calls[0]
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if function_name == "send_email":
            send_email(**arguments)
            break

        elif function_name == "summarize_latest_email":
            email_body = get_latest_email_body()
            summary = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system",
                        "content": "You are an assistant that summarizes emails."},
                    {"role": "user", "content": f"Summarize this email:\n\n{email_body}"}
                ]
            )
            print("\nEmail Summary:\n", summary.choices[0].message.content)
            break

    else:
        # GPT didn't call the function yet, continue interaction
        print("\n💬 Assistant's response:\n", choice_msg.content)
