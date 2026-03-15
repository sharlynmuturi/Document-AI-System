"""
Field extraction

Supports:
- Regex-based extraction
- Configuration via JSON
- BIO label generation for ML training
"""

import re
import json
from pathlib import Path


# Loading field patterns from JSON
CONFIG_PATH = Path("config/field_patterns.json")

if not CONFIG_PATH.exists():
    raise FileNotFoundError(f"Field configuration not found: {CONFIG_PATH}")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    FIELD_PATTERNS = json.load(f)



# Field extraction function
def extract_fields(text, doc_type="invoice"):
    """
    Extracts fields for a specific document type using regex patterns.
    """
    if doc_type not in FIELD_PATTERNS:
        raise ValueError(f"No patterns defined for document type '{doc_type}'")

    patterns = FIELD_PATTERNS[doc_type]
    results = {}

    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.MULTILINE)
        results[field] = match.group(1).strip() if match else None

    return results


# BIO label generation
def generate_bio_labels(tokens, extracted_fields):
    """
    Convert extracted values into BIO token labels for ML training.
    """
    labels = ["O"] * len(tokens)

    for field, value in extracted_fields.items():
        if not value:
            continue
        value_tokens = value.split()
        for i in range(len(tokens)):
            if tokens[i:i+len(value_tokens)] == value_tokens:
                labels[i] = f"B-{field.upper()}"
                for j in range(1, len(value_tokens)):
                    labels[i+j] = f"I-{field.upper()}"

    return labels