# Auto Mailer with Prompt Engineering & Function Calling

## Overview

This repository contains two Python scripts that implement an automated email system. The system leverages two different approaches to handle email sending and email summarization:

1. **LLaMA Model for Email Generation**: Uses prompt engineering to generate a complete email subject and body, based on a user's intent.
2. **OpenAI (GPT-4.1) for Function Calling**: Uses OpenAI's function calling feature to classify the user's intent (sending an email or summarizing an email) and trigger the corresponding action.

The goal is to allow the assistant to send personalized emails and summarize unread emails automatically by processing natural language inputs.

## Files

### 1. `practice.py` (LLaMA-based implementation)

- **Description**: This file uses the LLaMA model to generate the email subject and body based on the user's prompt.
- **Key Features**:
  - **Email Sending**: Uses SMTP to send emails.
  - **Email Fetching**: Retrieves the latest unread email and provides its summary.
  - **LLaMA Prompt**: Generates email content based on the intent specified by the user.
  - **Email Fallback**: If email content generation fails, it attempts to generate a valid email.

### 2. `practice.py` (OpenAI-based implementation)

- **Description**: This file uses OpenAI’s GPT-4.1 model for intent classification and function calling.
- **Key Features**:
  - **Email Sending**: Sends an email by calling the `send_email` function.
  - **Email Summarization**: Fetches the latest unread email and summarizes it using GPT-4.1.
  - **Function Calling**: Uses OpenAI’s function calling to determine whether the user wants to send an email or summarize the latest one.
  - **Input Handling**: The assistant continuously interacts with the user, parsing their requests and calling the appropriate function.

## Setup Instructions

### 1. Install Dependencies

You need to install the required dependencies. You can do this by running the following command:

pip install -r requirements.txt


The `requirements.txt` should include the following libraries:

- `requests`
- `smtplib`
- `imaplib`
- `openai`
- `python-dotenv`

### 2. Configuration

#### .env File

Create a `.env` file in the root directory of the project and add the following variables:

EMAIL_USER=your_email@example.com
EMAIL_PASS=your_email_password
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
GITHUB_TOKEN=your_openai_api_key


Make sure to replace the placeholder values with your actual credentials.

### 3. Running the Script

To run the LLaMA-based script:

python practice.py

To run the OpenAI-based script:

python practice.py


### 4. How It Works

#### LLaMA-based Script:
- The user enters a request to either send an email or summarize an email.
- If the email is incomplete, the system will attempt to generate the email subject and body using the LLaMA model.
- The email is then sent using SMTP, and the user is notified of the success or failure.

#### OpenAI-based Script:
- The assistant first classifies the user's intent (email sending or summarization).
- The assistant calls the appropriate function based on the user’s input: `send_email` or `summarize_latest_email`.
- If the function involves sending an email, the assistant collects the necessary details and sends the email via SMTP.
- If the user wants a summary, the assistant retrieves the latest unread email and summarizes it using GPT-4.1.

## Conclusion

This system is a simple but powerful way to automate email communication using natural language processing and function calling techniques from LLaMA and OpenAI's GPT models.

Feel free to modify and extend this system for different use cases, such as integrating it with a database or expanding the types of emails it can generate.
