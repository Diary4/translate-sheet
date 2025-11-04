# To run this code you need:
# pip install google-genai

import os
import csv
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

if __name__ == "__main__":
    input_csv = "Candles.csv"
    output_csv = "Candles_translated.csv"
    
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
    
    # Process each row and translate
    translated_rows = []
    total_rows = len(rows)
    
    for idx, row in enumerate(rows, 1):
        print(f"\n[{idx}/{total_rows}] Processing: {row.get('item_name', 'N/A')[:50]}...")
        
        # Translate description only
        direct_of_use = row.get('direct_of_use', '').strip()
        if direct_of_use:
            print(f"  Translating direct_of_use...")
            row['direct_of_use_arabic'] = translate(direct_of_use, "Arabic")
            row['direct_of_use_kurdish'] = translate(direct_of_use, "Kurdish (Sorani)")
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
