"""
Flow:
OCR - Regex extraction - SQLite storage - Excel export - RAG indexing
"""

import os
import cv2
from pathlib import Path
import pandas as pd

from scripts.ocr_layout import pdf_to_images, run_tesseract, process_ocr
from scripts.extraction import extract_fields
from scripts.mlops import log_extraction
from scripts.db_storage import init_db, create_document, save_fields, save_document_text
from scripts.rag_engine import index_document

init_db()


EXCEL_OUTPUT_BASE = Path("data/processed")
excel_data = {}


# Excel Helpers
def append_to_excel_data(document_id, filename, page_num, fields, confidences=None, sources=None):
    if confidences is None:
        confidences = {field: 1.0 for field in fields}
    if sources is None:
        sources = {field: "regex" for field in fields}

    for field, value in fields.items():
        if field not in excel_data:
            excel_data[field] = []
        excel_data[field].append({
            "document_id": document_id,
            "filename": filename,
            "page": page_num,
            "field_value": value,
            "confidence": confidences.get(field, 1.0),
            "source": sources.get(field, "regex")
        })


def write_excel(doc_type):
    """Writes Excel file inside the doc_type folder"""
    if not excel_data:
        print(f"No data to write for {doc_type}.")
        return

    # Create folder for this doc type
    output_folder = EXCEL_OUTPUT_BASE / doc_type
    output_folder.mkdir(parents=True, exist_ok=True)

    output_path = output_folder / f"processed_{doc_type}.xlsx"

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        for field, records in excel_data.items():
            df = pd.DataFrame(records)
            df.to_excel(writer, sheet_name=field[:31], index=False)

    print(f"Excel output saved: {output_path}")

    # Clear excel_data for next doc type
    excel_data.clear()


# Main pipeline
def process_document(path, doc_type="invoice"):
    """
    Full document processing workflow.

        path (str): Path to document file
        doc_type (str): Document type key (matches config JSON)
    """

    filename = os.path.basename(path)
    document_id = create_document(filename)
    pages = []
    full_text = ""

    images = pdf_to_images(path) if path.lower().endswith(".pdf") else [cv2.imread(path)]

    for i, image in enumerate(images, start=1):
        # OCR
        words, w, h = run_tesseract(image)
        processed = process_ocr(words, w, h)
        tokens = [w["text"] for w in processed]
        text = " ".join(tokens)

        # Save page text for RAG
        save_document_text(document_id, i, text)
        full_text += text + "\n"

        # Field extraction
        fields = extract_fields(text, doc_type=doc_type)

        # Save to database
        save_fields(
            document_id,
            fields,
            confidences={field: 1.0 for field in fields},
            sources={field: "regex" for field in fields}
        )

        # Accumulate Excel data
        append_to_excel_data(
            document_id,
            filename,
            i,
            fields,
            confidences={field: 1.0 for field in fields},
            sources={field: "regex" for field in fields}
        )

        # Log for MLOps
        log_extraction(filename, tokens, fields)

        pages.append({
            "page": i,
            "tokens": tokens,
            "fields": fields
        })

    # RAG indexing
    index_document(full_text, filename, "all", doc_type)

    return {
        "document_id": document_id,
        "file": filename,
        "pages": pages
    }