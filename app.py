# To run this code you need:
# pip install google-genai pandas openpyxl

import os
import pandas as pd
from google import genai
from google.genai import types

API_KEY = "AIzaSyDrYmMzDpPPCCKaxvR3uG_03NktfbS8Kkc"

client = genai.Client(api_key=API_KEY)

def translate_text(text, target_language):
    """Translate English text into target language using Gemini."""
    if not text or pd.isna(text):
        return ""

    model = "gemini-2.5-flash"

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(
                text=f"Translate the following English text into {target_language}. "
                     f"Return only the translated text, no explanations.\n\n{text}"
            )],
        ),
    ]

    try:
        response = client.models.generate_content(model=model, contents=contents)
        if response and response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text.strip()
    except Exception as e:
        print(f"⚠️ Error translating '{text[:40]}...': {e}")
    return ""

def translate_csv(input_path, output_path):
    """Read CSV, translate column, and save to new Excel file."""
    df = pd.read_csv(input_path)

    if "description" not in df.columns:
        print("❌ CSV must have a column named 'description'")
        return

    print("🔄 Translating... this may take a while")

    df["Arabic"] = df["description"].apply(lambda x: translate_text(x, "Arabic"))
    df["Kurdish (Sorani)"] = df["description"].apply(lambda x: translate_text(x, "Kurdish (Sorani)"))

    df.to_excel(output_path, index=False)
    print(f"✅ Translations saved to: {output_path}")

if __name__ == "__main__":
    input_csv = "Candles.csv"      # your input file
    output_excel = "translated.xlsx"  # output file
    translate_csv(input_csv, output_excel)
