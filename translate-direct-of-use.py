# To run this code you need:
# pip install google-genai

import os
import csv
import sys
import time
from google import genai
from google.genai import types

# Set your API key here (or as an environment variable)
API_KEY = "AIzaSyDrYmMzDpPPCCKaxvR3uG_03NktfbS8Kkc"

def translate(text, target_language):
    client = genai.Client(api_key=API_KEY)

    model = "gemini-2.5-flash"  # ✅ TEXT model (not -image)

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(
                text=f"Translate the following English text into {target_language}. "
                     f"Return only the translated text, no explanations.\n\n{text}"
            )],
        ),
    ]

    response = client.models.generate_content(
        model=model,
        contents=contents,
    )

    if response and response.candidates and response.candidates[0].content.parts:
        return response.candidates[0].content.parts[0].text
    return "[No translation]"

def translate_with_retry(text, target_language, max_attempts=5, backoff_seconds=2):
    """Translate with simple retry/backoff. If rate limited after max attempts, raise a sentinel error."""
    for attempt in range(1, max_attempts + 1):
        try:
            return translate(text, target_language)
        except Exception as e:
            message = str(e).lower()
            is_rate_limit = (
                "rate limit" in message
                or "429" in message
                or "resource exhausted" in message
                or "quota" in message
            )
            if not is_rate_limit:
                raise
            if attempt == max_attempts:
                print("\n⚠️ Rate limit exceeded after 5 attempts")
                # Raise a sentinel error we can catch to save progress & exit
                raise RuntimeError("Rate limit exceeded after 5 attempts")
            # Exponential backoff
            sleep_seconds = backoff_seconds * (2 ** (attempt - 1))
            time.sleep(sleep_seconds)

if __name__ == "__main__":
    input_csv = "Candles.csv"
    output_csv = "Candles_translated.csv"
    start_from_row = 39  # 1-based index
    
    # Read the CSV file
    rows = []
    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    # Add new columns for translations
    new_fieldnames = list(fieldnames)
    new_fieldnames.extend([
        "direct_of_use_arabic", "direct_of_use_kurdish"
    ])
    
    # Optionally preload existing output to reuse earlier rows
    existing_output_rows = []
    if os.path.exists(output_csv):
        try:
            with open(output_csv, "r", encoding="utf-8") as f_out:
                reader_out = csv.DictReader(f_out)
                existing_output_rows = list(reader_out)
        except Exception:
            existing_output_rows = []

    # Process each row and translate
    translated_rows = []
    total_rows = len(rows)
    
    def save_progress_and_exit():
        print(f"\n📝 Saving translations to {output_csv}...")
        with open(output_csv, "w", encoding="utf-8", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=new_fieldnames)
            writer.writeheader()
            writer.writerows(translated_rows)
        print(f"\n✅ Saved {len(translated_rows)} translated rows to {output_csv}")
        sys.exit(1)

    for idx, row in enumerate(rows, 1):
        # Reuse/skip until start_from_row - 1
        if idx < start_from_row:
            # Prefer the previously translated row if available
            if existing_output_rows and idx <= len(existing_output_rows):
                translated_rows.append(existing_output_rows[idx - 1])
            else:
                # Carry over the original row unchanged
                translated_rows.append(row)
            continue

        print(f"\n[{idx}/{total_rows}] Processing: {row.get('item_name', 'N/A')[:50]}...")

        # Translate description only
        direct_of_use = row.get('direct_of_use', '').strip()
        if direct_of_use:
            print(f"  Translating direct_of_use...")
            try:
                row['direct_of_use_arabic'] = translate_with_retry(direct_of_use, "Arabic")
                row['direct_of_use_kurdish'] = translate_with_retry(direct_of_use, "Kurdish (Sorani)")
            except RuntimeError as e:
                # Save partial progress and stop when rate limit warning occurs
                translated_rows.append(row)
                save_progress_and_exit()
        else:
            row['direct_of_use_arabic'] = ""
            row['direct_of_use_kurdish'] = ""

        translated_rows.append(row)
    
    # Write to new CSV file
    print(f"\n📝 Saving translations to {output_csv}...")
    with open(output_csv, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(translated_rows)
    
    print(f"\n✅ Successfully translated {total_rows} rows and saved to {output_csv}")
