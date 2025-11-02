import pandas as pd
from transformers import pipeline
from tqdm import tqdm

# --- Load translation models ---
translator_ar = pipeline("translation", model="Helsinki-NLP/opus-mt-en-ar")
translator_ku = pipeline("translation", model="Helsinki-NLP/opus-mt-en-ku")

# --- Step 1: Read the CSV file ---
input_file = "input.csv"   # change this to your file
df = pd.read_csv(input_file)

# --- Step 2: Select column to translate ---
column_to_translate = "Text"   # change to the column name containing English text

# --- Step 3: Add progress bar and translate ---
tqdm.pandas()

def translate_to_arabic(text):
    if pd.isna(text):
        return ""
    try:
        return translator_ar(text, max_length=400)[0]['translation_text']
    except Exception as e:
        print(f"Error (Arabic): {text} → {e}")
        return text

def translate_to_kurdish(text):
    if pd.isna(text):
        return ""
    try:
        return translator_ku(text, max_length=400)[0]['translation_text']
    except Exception as e:
        print(f"Error (Kurdish): {text} → {e}")
        return text

print("🔄 Translating English → Arabic...")
df["Arabic_Translation"] = df[column_to_translate].progress_apply(translate_to_arabic)

print("🔄 Translating English → Kurdish...")
df["Kurdish_Translation"] = df[column_to_translate].progress_apply(translate_to_kurdish)

# --- Step 4: Save to new Excel file ---
output_file = "translated_output.xlsx"
df.to_excel(output_file, index=False)

print(f"✅ Done! Translations saved to {output_file}")
