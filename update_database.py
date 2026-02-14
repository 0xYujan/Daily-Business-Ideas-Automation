import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "ideas_database.json"
FRESH_FILE = BASE_DIR / "fresh_ideas.json"

def main():
    if not FRESH_FILE.exists():
        print("❌ fresh_ideas.json not found!")
        return

    with open(DB_FILE, "r", encoding="utf-8") as f:
        existing = json.load(f)
    
    with open(FRESH_FILE, "r", encoding="utf-8") as f:
        fresh = json.load(f)

    # Mark fresh ideas as priority
    for idea in fresh:
        idea["priority"] = True
    
    # Check for duplicates by ID
    existing_ids = {i["id"] for i in existing}
    added_count = 0
    
    for idea in fresh:
        if idea["id"] not in existing_ids:
            existing.append(idea)
            added_count += 1
            print(f"➕ Added: {idea['business_name']}")
        else:
            print(f"⚠ Skipped duplicate: {idea['business_name']}")
    
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Successfully added {added_count} new ideas to database.")
    print(f"📊 Total Database Size: {len(existing)} ideas")

if __name__ == "__main__":
    main()
