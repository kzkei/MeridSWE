"""Layer 1 funcs: verify dataset correctness and compute hash"""
import hashlib
import json
from pathlib import Path
import base64

RECORDS_FILE = Path("data/layer1/records.json")
BATCH_DIR = Path("data/layer1/batches")

EXPECTED_COUNT = 500
BATCH_RANGES = ["0-99", "100-199", "200-299", "300-399", "400-499"]


def load_records(path: Path = RECORDS_FILE):
    """To verify fetched and saved"""

    records = json.loads(path.read_text())
    # double check for legnth (safety)
    if len(records) != EXPECTED_COUNT:
        raise RuntimeError(f"Expected {EXPECTED_COUNT} records, got {len(records)}")
    return records

def compute_content_hash(records: list[str], separator: str = ""):
    """SHA256 of joined record strings (default: no separator)"""

    payload = separator.join(records).encode()

    return hashlib.sha256(payload).hexdigest()

def hash_raw_batches(batch_dir: Path = BATCH_DIR):
    """SHA256 of exact API response bytes - concatenated in order."""
    all_bytes = b"".join(
        (batch_dir / f"range_{r}.json").read_bytes() for r in BATCH_RANGES
    )

    return hashlib.sha256(all_bytes).hexdigest()

def hash_records_file(path: Path = RECORDS_FILE):
    """SHA256 of records.json exactly as saved """

    return hashlib.sha256(path.read_bytes()).hexdigest()

def hash_decoded_binary(records: list[str]) -> str:
    """SHA256 of base64 decoded record bytes concatenated in order"""

    decoded = b"".join(base64.b64decode(r) for r in records)

    return hashlib.sha256(decoded).hexdigest()

def verify_and_hash(path: Path = RECORDS_FILE):
    """To load all, verify count, return hash"""

    records = load_records(path)

    return {
        "record_count": len(records),
        "hash_joined": compute_content_hash(records),
        "hash_newline": compute_content_hash(records, separator="\n"),
        "hash_raw_batches": hash_raw_batches(),
        "hash_records_file": hash_records_file(path),
        "hash_decoded_binary": hash_decoded_binary(records),
    }

# script flow - print hashes
if __name__ == "__main__":
    result = verify_and_hash()
    print(result)