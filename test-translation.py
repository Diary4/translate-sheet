# To run this code you need:
# pip install google-genai

import os
import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types

# Set your API key here (or as an environment variable)
API_KEY = "AIzaSyDrYmMzDpPPCCKaxvR3uG_03NktfbS8Kkc"

def translate(text, target_language, max_retries=5):
    """Translate text with retry logic for rate limiting"""
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

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
            )

            if response and response.candidates and response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].text
            return "[No translation]"
            
        except Exception as e:
            error_str = str(e)
            # Check if it's a rate limit error (429)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if attempt < max_retries - 1:
                    # Exponential backoff: 2s, 4s, 8s, 16s, 32s
                    wait_time = 2 ** (attempt + 1)
                    time.sleep(wait_time)
                    continue
                else:
                    return f"[Rate limit exceeded after {max_retries} attempts]"
            else:
                # For other errors, retry once with delay
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    return f"[Translation failed: {error_str[:50]}]"
    
    return "[Translation failed]"

def translate_row(row_data):
    """Translate a single row's description. Returns (index, translated_row)"""
    idx, row = row_data
    description = row.get('description', '').strip()
    
    if description:
        # Translate Arabic
        row['description_arabic'] = translate(description, "Arabic")
        # Small delay between translations to avoid rate limits
        time.sleep(0.5)
        # Translate Kurdish
        row['description_kurdish'] = translate(description, "Kurdish (Sorani)")
    else:
        row['description_arabic'] = ""
        row['description_kurdish'] = ""
    
    return (idx, row)

if __name__ == "__main__":
    input_csv = "Dermocosmetics.csv"
    output_csv = "Dermocosmetics_translated.csv"
    
    # Read the CSV file
    rows = []
    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    # Add new columns for translations
    new_fieldnames = list(fieldnames)
    new_fieldnames.extend([
        "description_arabic", "description_kurdish"
    ])
    
    total_rows = len(rows)
    print(f"🚀 Starting translation of {total_rows} rows using parallel processing...")
    
    # Process rows in parallel
    translated_rows = [None] * total_rows  # Pre-allocate list to maintain order
    
    # Use ThreadPoolExecutor for parallel processing
    # Reduced workers to avoid rate limiting (429 errors)
    max_workers = 3  # Process 3 rows concurrently to respect rate limits
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all translation tasks
        future_to_row = {
            executor.submit(translate_row, (idx, row)): idx 
            for idx, row in enumerate(rows)
        }
        
        # Process completed translations
        completed = 0
        for future in as_completed(future_to_row):
            completed += 1
            try:
                idx, translated_row = future.result()
                translated_rows[idx] = translated_row
                item_name = translated_row.get('item_name', 'N/A')[:50]
                print(f"[{completed}/{total_rows}] ✅ Completed: {item_name}...")
            except Exception as e:
                original_idx = future_to_row[future]
                print(f"[{completed}/{total_rows}] ❌ Error processing row {original_idx}: {str(e)[:50]}")
                # Keep original row with empty translations
                rows[original_idx]['description_arabic'] = "[Translation failed]"
                rows[original_idx]['description_kurdish'] = "[Translation failed]"
                translated_rows[original_idx] = rows[original_idx]
    
    # Write to new CSV file
    print(f"\n📝 Saving translations to {output_csv}...")
    with open(output_csv, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(translated_rows)
    
    print(f"\n✅ Successfully translated {total_rows} rows and saved to {output_csv}")
