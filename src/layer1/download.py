"""Fetch dataset in batches and downloads all"""
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from utils.client import ApiClient
from utils.log_config import setup_logging

BATCH_RANGES = [(0,99), (100,199), (200,299), (300,399), (400,499)]

def fetch_batch(client: ApiClient, start: int, end: int):
    """To fetch one batch at a time, rety if limit reached"""
    path = f"/api/v1/dataset?batch=true&range={start}-{end}"

    while True:
        response = client.request("GET", path)

        # retry if 429
        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", "1"))
            print(f"Rate limited on {start}-{end}, sleeping {wait}s...")
            time.sleep(wait)
            continue
        # 
        if response.status_code != 200:
            raise RuntimeError(
                f"Batch {start}-{end} failed: {response.status_code} {response.text}"
            )
        
        remaining = response.headers.get("ratelimit-remaining")
        if remaining == "0":
            time.sleep(1)  # wait for reset

        return response.content

def download(client: ApiClient):
    """To fetch batches, download all, return all"""
    
    Path("data/layer1/batches").mkdir(parents=True, exist_ok=True)

    results: list[str] = []

    for start, end in BATCH_RANGES:

        print(f"fetching range {start}-{end}")

        # fetch batch with range specified
        raw_bytes = fetch_batch(client, start, end)

        # save response bytes
        batch_file = Path("data/layer1/batches") / f"range_{start}-{end}.json"
        batch_file.write_bytes(raw_bytes)

        print(f"saved {batch_file} ({len(raw_bytes)} bytes)")

        # parse and collect records
        batch_json = json.loads(raw_bytes)
        records = batch_json["data"]

        print(f"got {len(records)} records")

        # append results
        results.extend(records)

    # save dataset together in records.json
    Path("data/layer1/records.json").parent.mkdir(parents=True, exist_ok=True)
    Path("data/layer1/records.json").write_text(json.dumps(results))

    print(f"saved with ({len(results)} records total)")

    # assert for correctness
    if len(results) != 500:
        raise RuntimeError(f"Expected 500 records, got {len(results)}")
    return results

# define script flow using fetch and download
if __name__ == "__main__":
    load_dotenv(find_dotenv())
    setup_logging()

    # init an api client
    client = ApiClient(os.environ["BASE_URL"], os.environ["API_KEY"])

    # fetch and download
    results = download(client=client)

    print(f"finished with {len(results)} results")

