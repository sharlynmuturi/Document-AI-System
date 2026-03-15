import sqlite3
from scripts.rag_engine import retrieve_context, ask_llm

DB_PATH = "document_ai.db"


# SQL Helpers
def query_invoices(filter_type="all", threshold=None):
    """
    Returns invoices based on filter type:
    - "count_over": returns count and filenames above threshold
    - "highest": returns invoice with highest total
    - "all": returns all invoices
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT d.filename, f.field_value
        FROM extracted_fields f
        JOIN documents d ON f.document_id = d.id
        WHERE f.field_name='total_amount'
    """)
    rows = cur.fetchall()
    conn.close()

    invoices = []
    for filename, value in rows:
        try:
            v = float(str(value).replace("$", "").replace(",", ""))
            invoices.append((filename, v))
        except:
            continue

    if filter_type == "count_over" and threshold is not None:
        results = [(f, v) for f, v in invoices if v > threshold]
        return results

    if filter_type == "highest":
        if invoices:
            best = max(invoices, key=lambda x: x[1])
            return best
        return None

    return invoices



# Hybrid Document AI engine
def ask_document_ai(question, doc_type):
    q = question.lower()

    # Structured invoice queries
    if "invoice" in q:
        if "how many" in q or "count" in q:
            # Detect threshold
            import re
            m = re.search(r"\$(\d+(?:,\d{3})*)", question)
            threshold = float(m.group(1).replace(",", "")) if m else 0
            results = query_invoices(filter_type="count_over", threshold=threshold)
            files = [f for f, v in results]
            return f"{len(results)} invoices exceed ${threshold}\n" + "\n".join(files)

        if "highest" in q or "largest" in q:
            best = query_invoices(filter_type="highest")
            if best:
                return f"The invoice with the highest amount is {best[0]} with ${best[1]:,.2f}"
            return "No invoice amounts found."

        if "list" in q or "all" in q:
            invoices = query_invoices()
            return "All invoices:\n" + "\n".join([f"{f}: ${v:,.2f}" for f, v in invoices])

    # Structured resume queries
    if "resume" in q or "skill" in q or "python" in q:
        context, sources = retrieve_context(question, doc_type="resume")
        answer = ask_llm(question, context, "resume")
        return answer

    # Default: unstructured RAG + LLM
    context, sources = retrieve_context(question, doc_type=doc_type)
    answer = ask_llm(question, context, doc_type)
    return answer