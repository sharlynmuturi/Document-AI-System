"""
run_pipeline.py

Runs the full document processing pipeline
on all files in the raw data folders (supports multiple document types).
"""

from pathlib import Path
import pickle
from scripts.pipeline import process_document, write_excel

DATA_FOLDERS = {
    "invoice": Path("data/raw/invoices"),
    "resume": Path("data/raw/resumes"),
}

PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

VALID_EXTS = [".pdf", ".png", ".jpg", ".jpeg", ".tiff"]

all_results = []

# -------------------------
# Loop through document types
# -------------------------
for doc_type, folder in DATA_FOLDERS.items():
    files = [f for f in folder.rglob("*") if f.suffix.lower() in VALID_EXTS]
    print(f"\nFound {len(files)} {doc_type} documents in {folder}")

    for i, file_path in enumerate(files, start=1):
        try:
            print(f"[{i}/{len(files)}] Processing {doc_type}: {file_path.name}")
            result = process_document(str(file_path), doc_type=doc_type)
            all_results.append(result)
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

    # Write Excel for all documents of this type
    write_excel(doc_type)

# -------------------------
# Save results for ML training / debugging
# -------------------------
pickle_path = PROCESSED_DIR / "all_results.pkl"
with open(pickle_path, "wb") as f:
    pickle.dump(all_results, f)

print("\nPipeline finished")
print(f"Processed documents: {len(all_results)}")
print(f"Results saved to: {pickle_path}")