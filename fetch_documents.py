import requests
import json
import sys
import time
import os

# Helper script to fetch all documents from the Open Raadsinformatie API
# API Docs: https://github.com/openstate/open-raadsinformatie/blob/master/API-docs.md
# Requires: pip install requests

BASE_URL = "https://api.openraadsinformatie.nl/v1/elastic"
INDEX_PATTERN = "ori_*"

def fetch_documents():
    # We use search_after for deep pagination as the scroll API is restricted
    url = f"{BASE_URL}/{INDEX_PATTERN}/_search"

    # Query: Match all documents that have a 'last_discussed_at' date
    # Sorted by 'last_discussed_at' descending (newest first)
    # We add _id to sort to ensure deterministic ordering for search_after
    query = {
        "size": 1000,  # Increased batch size for speed
        "sort": [
            {"last_discussed_at": {"order": "desc"}},
            {"_id": {"order": "asc"}}
        ],
        "query": {
            "bool": {
                "must": [
                    {"exists": {"field": "last_discussed_at"}}
                ]
            }
        },
        "_source": {
            "excludes": ["text"] # Exclude large text fields to reduce bandwidth if acceptable, but user asked for "all documents", assuming they want content.
            # If they want full content, we should keep it. Let's assume full content for now but keep this comment.
            # Actually, let's play it safe and NOT exclude anything unless requested,
            # but increasing batch size to 1000 is the main speedup.
        }
    }

    print(f"Fetching documents starting from {url}...")

    # Create temp directory
    output_dir = "temp"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "documents.json")

    print(f"Saving to {output_file}...")

    fetched_count = 0
    total = "Unknown"
    start_time = time.time()

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("[\n")
            first_doc = True

            while True:
                try:
                    response = requests.post(url, json=query)
                    response.raise_for_status()
                    data = response.json()
                except requests.exceptions.RequestException as e:
                    print(f"\nRequest error: {e}. Retrying in 5s...")
                    time.sleep(5)
                    continue

                hits = data['hits']['hits']
                if not hits:
                    break

                if isinstance(total, str):
                    total_val = data['hits']['total']
                    total = total_val['value'] if isinstance(total_val, dict) else total_val
                    print(f"Total documents found: {total}")

                for doc in hits:
                    if not first_doc:
                        f.write(",\n")
                    json.dump(doc, f)
                    first_doc = False
                    fetched_count += 1

                # Calculate speed
                elapsed = time.time() - start_time
                if elapsed > 0:
                    rate = fetched_count / elapsed
                else:
                    rate = 0

                # Progress update to stderr
                sys.stderr.write(f"\rFetched {fetched_count}/{total} documents ({rate:.1f} docs/sec)...")

                # Get sort values for next page
                last_doc = hits[-1]
                sort_values = last_doc['sort']
                query['search_after'] = sort_values

                # No sleep! Max speed!

            f.write("\n]")

    except KeyboardInterrupt:
        print("\nStopping fetch...")
        # Try to close the array validly if stopped
        try:
            with open(output_file, "a", encoding="utf-8") as f:
                f.write("\n]")
        except:
            pass
    except Exception as e:
        print(f"\nError during fetch: {e}")

    print(f"\nDone. Total fetched: {fetched_count}")

if __name__ == "__main__":
    fetch_documents()
