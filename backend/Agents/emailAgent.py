import base64
import os
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import openai
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from database import fetch_patients_data
import json
import gradio as gr

# Load OpenAI API key from credentials.json
with open('credentials.json', 'r') as f:
    credentials = json.load(f)
openai.api_key = credentials['installed']['openAI_api_key']
print(openai.api_key)
# --- Setup ---
SCOPES = ['https://www.googleapis.com/auth/calendar']
# --- Authenticate with Gmail API ---
def authenticate():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)
# --- Send Email ---
def send_email(service, text):
    message = MIMEMultipart('alternative')
    message['To'] = 'sorhanft@gmail.com'
    message['From'] = 'me'
    message['Subject'] = 'Your Billing Statement from Bayfront Urgent Care'
    html = """
    <html>
    <body>
        <h2>Bayfront Urgent Care</h2>
        <p>Your Billing Statement</p>
        <ul>
            <li>Exam, Blood work, Cholesterol, BMI</li>
        </ul>
        <p><strong>Your Responsibility: $100.00</strong></p>
        <a href="https://example.com/pay">Pay Now</a>
    </body>
    </html>
    """
    message.attach(MIMEText(html, 'html'))
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    send_body = { 'raw': encoded_message }
    sent = service.users().messages().send(userId="me", body=send_body).execute()
    print(f"✅ Sent email ID: {sent['id']}")

# --- Get full text from reply ---
def get_body_from_message(message):
    payload = message.get('payload', {})
    parts = payload.get('parts')
    if parts:
        for part in parts:
            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                return base64.urlsafe_b64decode(part['body']['data']).decode()
    elif 'data' in payload.get('body', {}):
        return base64.urlsafe_b64decode(payload['body']['data']).decode()
    return ''
def agent_response_generator(prompt):
    # Create a chat completion request using new OpenAI API format
    response = openai.chat.completions.create(
        model='gpt-4',
        messages=[
            {"role": "system", "content": "You're a helpful and polite assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    # Extract and return the response text (updated syntax)
    return response.choices[0].message.content.strip()
# --- Check for Replies ---
def check_replies(service):
    today = datetime.today().strftime('%Y/%m/%d')
    query = f"is:unread after:{today}"

    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q=query).execute()
    messages = results.get('messages', [])

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = msg_data['payload']['headers']
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
        thread_id = msg_data['threadId']
        reply_body = get_body_from_message(msg_data)

        print(f"\n🔁 Reply from: {sender}")
        print(f"📬 Subject: {subject}")
        print(f"✉️ Message: {reply_body}")

        # AI-generated reply (updated syntax)
        ai_reply = openai.chat.completions.create(
            model='gpt-4',
            messages=[
                {"role": "system", "content": "You're a helpful and polite medical billing assistant."},
                {"role": "user", "content": reply_body}
            ]
        )
        reply_text = ai_reply.choices[0].message.content.strip()

        send_reply(service, thread_id, sender, reply_text)

        # Mark message as read
        service.users().messages().modify(userId='me', id=msg['id'], body={'removeLabelIds': ['UNREAD']}).execute()
        
# --- Send AI Reply ---
def send_reply(service, thread_id, to_email, text):
    message = MIMEText(text)
    message['To'] = to_email
    message['From'] = 'me'
    message['Subject'] = 'Re: Your Billing Statement'

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {
        'raw': encoded_message,
        'threadId': thread_id
    }

    sent = service.users().messages().send(userId='me', body=body).execute()
    print(f"✅ Replied to {to_email} in thread {thread_id}")

def gradio_show_patients():
    data = fetch_patients_data()
    if not data:
        return [["No data found"]]
    return data

def gradio_generate_email_response(index):
    data = fetch_patients_data()
    if not data or index >= len(data):
        return "No patient found for that index."
    record = data[index]
    clinic_name = 'Bayfront Urgent Care'
    first_name = record[1]
    last_name = record[2]
    visit_date = record[9]
    reason_for_visit = record[10]
    visit_type = record[11]
    insurance_provider = record[12]
    insurance_status = record[14]
    bill_amount = record[18]
    bill_paid = record[20]
    bill_date = record[19]
    conversation_history = record[27]
    reply_pending = record[24]
    last_patient_reply = record[29]

    prompt = f"""
    You are a friendly billing assistant for a {clinic_name} clinic. You are contacting {first_name} {last_name} about a visit they had on {visit_date} for {reason_for_visit.lower()} ({visit_type}). You can make this intro smooth, kind and caring.

    Their insurance provider was {insurance_provider} ({insurance_status}). After processing, the remaining balance is ${bill_amount:.2f} and payment has not been received. Welcome to include any of these information when the patient chats to you.

    Kindly initiate a professional and polite message explaining the situation. Let them know they can respond with questions or make a payment through the clinic's billing portal.

    Do not pressure them. Keep the tone supportive and clear.

    If this is not the first intro reachout, "conversation_history" and "last_patient_reply" would have the context of the conversation so far.

    So you can look at all the info and conversation, then reply to their last_patient_reply.
    """
    response = agent_response_generator(prompt)
    return response

with gr.Blocks() as demo:
    gr.Markdown("# Patient Billing Assistant")
    patients = gr.Dataframe(
        value=gradio_show_patients(),
        label="Patients Data"
    )
    gr.Markdown("## Generate Email Response for Patient Index")
    index_input = gr.Number(label="Patient Index (row number)", value=0)
    response_output = gr.Textbox(label="Generated Email Response")
    generate_btn = gr.Button("Generate Email Response")
    generate_btn.click(fn=gradio_generate_email_response, inputs=index_input, outputs=response_output)

if __name__ == '__main__':
    demo.launch() 