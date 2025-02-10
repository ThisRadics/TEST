import streamlit as st
import os
import datetime
import time
import base64
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- Configuration Constants ---
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]
SPREADSHEET_ID = '10lbi8VTEZ1i7a21XghH8PyQmJQkSLupJDGmMqBIGsw4'
SHEET_NAME = 'Notification Manager'
CREDENTIALS_FILE = r'C:\Users\DELL\Desktop\PYTHON DIRECTORY\SAFEBOX NOTIFICATION SYSTEM\credentials.json'

# Predefined dropdown options for the "Recipient Sheet"
RECIPIENTS_OPTIONS = ["Employee Master Data", "Zummey", "SafeBox Energy", "Admin Master Data"]

# --- Google API Service Functions ---

@st.cache_resource
def get_sheets_service():
    """Returns an authorized Google Sheets API service instance."""
    if not os.path.exists(CREDENTIALS_FILE):
        st.error(f"Google Sheets API credentials not found at: {CREDENTIALS_FILE}")
        st.stop()
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service

@st.cache_resource
def get_drive_service():
    """Returns an authorized Google Drive API service instance."""
    if not os.path.exists(CREDENTIALS_FILE):
        st.error(f"Google Drive API credentials not found at: {CREDENTIALS_FILE}")
        st.stop()
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    return drive_service

def append_notification_row(service, data):
    """
    Appends a row of data to the specified sheet.
    Data format: [Notification Type, Recipient Sheet, Notification Message, Notification Date, Prompt]
    """
    range_ = f'{SHEET_NAME}!A:E'
    body = {'values': [data]}
    response = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=range_,
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()
    return response

def upload_file_to_drive(uploaded_file):
    """
    Uploads a non-image file to Google Drive, sets its permission to public (reader),
    and returns the shareable link.
    """
    drive_service = get_drive_service()
    file_metadata = {
        'name': uploaded_file.name,
        'mimeType': uploaded_file.type
    }
    media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }
    drive_service.permissions().create(fileId=file_id, body=permission).execute()
    file_info = drive_service.files().get(fileId=file_id, fields='webViewLink').execute()
    return file_info.get('webViewLink')

def build_final_message(text, uploaded_files, attachment_position):
    """
    Constructs the final HTML message.
    - The notification text is wrapped in a justified paragraph.
    - For image files: embeds each image as a data URI.
      If the attachment position is "Top", images are placed above the text; if "Bottom", below the text.
    - For non-image files: uploads each file to Drive and appends a download link (left-aligned) after the text.
    - Appends a left-aligned closing signature ("Best regards, Safebox Technologies")
      only if the text does not already include it.
    """
    body_html = f'<p style="text-align: justify; margin: 0;">{text}</p>'
    
    images_html = ""
    non_image_html = ""
    
    if uploaded_files:
        for file in uploaded_files:
            if file.type.startswith("image/"):
                img_bytes = file.getvalue()
                encoded = base64.b64encode(img_bytes).decode()
                mime_type = file.type
                images_html += f'<img src="data:{mime_type};base64,{encoded}" style="max-width:100%; margin-bottom:10px;"><br>'
            else:
                link = upload_file_to_drive(file)
                non_image_html += f'<a href="{link}" target="_blank">Download {file.name}</a><br>'
    
    if images_html:
        if attachment_position == "Top":
            final_message = f"<div style='text-align: center;'>{images_html}</div>{body_html}"
        else:
            final_message = f"{body_html}<div style='text-align: center;'>{images_html}</div>"
    else:
        final_message = body_html
    
    if non_image_html:
        final_message += f"<div style='text-align: left; margin-top: 10px;'>{non_image_html}</div>"
    
    if "Best regards" not in text:
        final_message += "<div style='text-align: left;'>Best regards,<br>Peace Ekeinde<br>Safebox Technologies</div>"
    
    return final_message

# --- Page Layout Functions ---

def landing_page():
    st.image("https://via.placeholder.com/300x100.png?text=Company+Logo", width=300)
    st.markdown("<h1 style='text-align: center;'>SAFEBOX NOTIFICATION SYSTEM</h1>", unsafe_allow_html=True)
    st.write("Select the mode you want to use:")

    with st.sidebar:
        st.header("Instructions")
        st.write("""
        **How to use this system:**
        1. **Select a Mode:** Choose between *Instant Messaging* or *Scheduling Message*.
        2. **Instant Messaging:** Immediately send out notifications.
        3. **Scheduling Message:** Schedule notifications to be sent on a future date.
        4. **Fill in the Form:** Enter the required details.
        5. **Attach Files (Optional):** Upload one or more attachments. For images, you can choose their position (Top or Bottom).
        6. **Send:** Click the send button.
        """)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Instant Messaging"):
            with st.spinner("Redirecting to Instant Messaging..."):
                time.sleep(1)
            st.session_state.page = "instant"
            st.rerun()
    with col2:
        if st.button("Scheduling Message"):
            with st.spinner("Redirecting to Scheduling Message..."):
                time.sleep(1)
            st.session_state.page = "scheduling"
            st.rerun()

def instant_messaging_page():
    if st.button("← Go Back"):
        st.session_state.page = "landing"
        st.rerun()

    st.markdown("<h1 style='text-align: center;'>Instant Messaging</h1>", unsafe_allow_html=True)
    st.write("Fill in the details below to send your notification immediately.")

    with st.form(key="instant_messaging_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            notification_type = st.text_input("Subject")
        with col2:
            recipients_sheet = st.selectbox("Recipient Sheet", RECIPIENTS_OPTIONS)
        with col3:
            notification_date = st.date_input("Notification Date", value=datetime.date.today())
        
        uploaded_files = st.file_uploader("Upload Attachments (optional)", accept_multiple_files=True)
        image_files = [f for f in uploaded_files if f.type.startswith("image/")] if uploaded_files else []
        attachment_position = None
        if image_files:
            attachment_position = st.radio("Attachment Position", options=["Top", "Bottom"])
        
        notification_message = st.text_area("Notification Message", height=150)
        
        cols = st.columns(3)
        with cols[1]:
            submit_button = st.form_submit_button("Send Notification")

    if submit_button:
        with st.spinner("Sending notification..."):
            time.sleep(1)
        date_str = notification_date.strftime("%Y-%m-%d")
        final_message = build_final_message(notification_message, uploaded_files, attachment_position)
        row_data = [notification_type, recipients_sheet, final_message, date_str, "send"]

        service = get_sheets_service()
        try:
            append_notification_row(service, row_data)
            st.success("Notification sent successfully!")
        except Exception as e:
            st.error(f"An error occurred while sending the notification: {e}")

def scheduling_message_page():
    if st.button("← Go Back"):
        st.session_state.page = "landing"
        st.rerun()

    st.markdown("<h1 style='text-align: center;'>Scheduling Message</h1>", unsafe_allow_html=True)
    st.write("Fill in the details below to schedule your notification. The message will trigger on the set date.")

    with st.form(key="scheduling_message_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            notification_type = st.text_input("Subject (Notification Type)")
        with col2:
            recipients_sheet = st.selectbox("Recipient Sheet", RECIPIENTS_OPTIONS)
        with col3:
            notification_date = st.date_input("Scheduled Date", value=datetime.date.today())
        
        uploaded_files = st.file_uploader("Upload Attachments (optional)", accept_multiple_files=True, key="scheduling_upload")
        image_files = [f for f in uploaded_files if f.type.startswith("image/")] if uploaded_files else []
        attachment_position = None
        if image_files:
            attachment_position = st.radio("Attachment Position", options=["Top", "Bottom"], key="scheduling_position")
        
        notification_message = st.text_area("Notification Message", height=150)
        
        cols = st.columns(3)
        with cols[1]:
            submit_button = st.form_submit_button("Send Notification")

    if submit_button:
        today = datetime.date.today()
        if notification_date <= today:
            st.error("Error: Please set a future date for scheduling or go back to use the Instant Messaging interface.")
            return

        with st.spinner("Scheduling notification..."):
            time.sleep(1)
        date_str = notification_date.strftime("%Y-%m-%d")
        final_message = build_final_message(notification_message, uploaded_files, attachment_position)
        row_data = [notification_type, recipients_sheet, final_message, date_str, "send"]

        service = get_sheets_service()
        try:
            append_notification_row(service, row_data)
            st.success(f"Notification scheduled successfully for {date_str}!")
        except Exception as e:
            st.error(f"An error occurred while scheduling the notification: {e}")

def main():
    if "page" not in st.session_state:
        st.session_state.page = "landing"

    if st.session_state.page == "landing":
        landing_page()
    elif st.session_state.page == "instant":
        instant_messaging_page()
    elif st.session_state.page == "scheduling":
        scheduling_message_page()

if __name__ == "__main__":
    main()










