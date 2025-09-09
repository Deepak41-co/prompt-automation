import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
from datetime import datetime

# ===== CONFIG =====
SHEET_ID = "1zgKG9VEw4Q30leUww9lgoorvYqPEYQplqamgI_sYHIw"  # replace with your Google Sheet ID if different

# ===== check secrets =====
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Missing GEMINI_API_KEY in secrets. Add GEMINI_API_KEY to .streamlit/secrets.toml or Streamlit Secrets.")
    st.stop()

if "google_service_account" not in st.secrets:
    st.error("Missing google_service_account in secrets. Add your service account JSON fields under [google_service_account].")
    st.stop()

# ===== Configure Gemini client =====
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ===== Google Sheets creds from secrets =====
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds_dict = dict(st.secrets["google_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

# Authorize gspread client and open the sheet
gspread_client = gspread.authorize(creds)
sheet = gspread_client.open_by_key(SHEET_ID).sheet1  # single-tab sheet

# ===== Few-Shot Examples =====
FEW_SHOT = """ ... your examples ... """

# ===== Streamlit UI =====
st.title("✨ Character Prompt Generator (Gemini + Google Sheets)")

with st.form("character_form"):
    name = st.text_input("Full Name")
    dob = st.text_input("Date of Birth (e.g., 24 February 1984)")
    pob = st.text_input("Place of Birth")
    profession = st.text_input("Profession")
    submitted = st.form_submit_button("Generate Prompt")

if submitted:
    # Construct prompt for Gemini
    base_prompt = f"""
{FEW_SHOT}

Now follow the same style and generate a new prompt.

Input:
Name: {name}
Date of Birth: {dob}
Place of Birth: {pob}
Profession: {profession}

Output:
"""
    try:
        with st.spinner("Generating prompt..."):
            model = genai.GenerativeModel("gemini-2.5-pro")
            response = model.generate_content(base_prompt)

        # Safely extract text
        if hasattr(response, "text") and response.text:
            generated = response.text
        elif hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            generated = getattr(candidate, "content", None) or getattr(candidate, "text", "")
        else:
            generated = str(response)

        generated = generated.strip()

        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Row data (id left empty)
        row_data = [
            "",             # id
            name,           # name
            generated,      # prompt
            "",             # img
            "",             # description
            "",             # native_language
            "",             # is_multilingual
            timestamp,      # created_at
            ""              # category
        ]

        # Save row in Google Sheet
        sheet.append_row(row_data)

        st.success("✅ Prompt generated and saved to Google Sheets!")
        st.text_area("Generated Prompt", generated, height=300)

    except Exception as e:
        st.error("Error generating or saving the prompt. See details below.")
        st.exception(e)
