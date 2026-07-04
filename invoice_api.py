"""
Invoice extraction API for the Anthrasync Task 1 workflow.
Exposes POST /extract-invoice : takes raw invoice text, returns structured JSON.
"""
import os
import re
import json
import logging

from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("invoice_api")

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("No Gemini API key found. Set GEMINI_API_KEY in your .env file.")

genai.configure(api_key=API_KEY)
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
model = genai.GenerativeModel(MODEL_NAME)

app = FastAPI(title="Invoice Extraction API")


class InvoiceIn(BaseModel):
    text: str


EXTRACTION_PROMPT = """You are an expert invoice data extraction system.
Read the invoice text below and return ONLY a valid JSON object - no markdown, no code fences, no commentary.

Use exactly these keys (camelCase). If a value is missing, use "" for text and 0 for numbers:
{
  "vendor": "",
  "vendorUid": "",
  "vendorIban": "",
  "invoiceNumber": "",
  "invoiceDate": "",
  "dueDate": "",
  "netAmount": 0,
  "vatAmount": 0,
  "vatPercentage": 0,
  "grossAmount": 0,
  "currency": "",
  "costCenter": "",
  "lineItems": [
    {"description": "", "quantity": 0, "unitPrice": 0, "amount": 0}
  ],
  "confidenceScore": 0,
  "anomalies": []
}

Rules:
- Dates in YYYY-MM-DD format if possible.
- Numbers as plain numbers (no currency symbols, no commas).
- confidenceScore is your own confidence between 0 and 1.
- anomalies is a list of short strings describing anything suspicious. Empty list if none.

Invoice text:
---
{invoice_text}
---
"""


def _clean_json(raw: str) -> dict:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def _to_number(value):
    try:
        return float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0


def _clean_data(data: dict) -> dict:
    result = {
        "vendor": data.get("vendor", "") or "",
        "vendorUid": data.get("vendorUid", "") or "",
        "vendorIban": data.get("vendorIban", "") or "",
        "invoiceNumber": data.get("invoiceNumber", "") or "",
        "invoiceDate": data.get("invoiceDate", "") or "",
        "dueDate": data.get("dueDate", "") or "",
        "netAmount": _to_number(data.get("netAmount", 0)),
        "vatAmount": _to_number(data.get("vatAmount", 0)),
        "vatPercentage": _to_number(data.get("vatPercentage", 0)),
        "grossAmount": _to_number(data.get("grossAmount", 0)),
        "currency": data.get("currency", "") or "",
        "costCenter": data.get("costCenter", "") or "",
        "confidenceScore": _to_number(data.get("confidenceScore", 0)),
        "anomalies": data.get("anomalies", []) or [],
    }

    items = []
    for it in (data.get("lineItems") or []):
        if not isinstance(it, dict):
            continue
        desc = (it.get("description") or "").strip()
        qty = _to_number(it.get("quantity", 0))
        if not desc and qty == 0:
            continue
        items.append({
            "description": desc,
            "quantity": qty,
            "unitPrice": _to_number(it.get("unitPrice", 0)),
            "amount": _to_number(it.get("amount", 0)),
        })
    result["lineItems"] = items

    expected = round(result["netAmount"] + result["vatAmount"], 2)
    if result["grossAmount"] and abs(expected - result["grossAmount"]) > 0.5:
        result["anomalies"].append(
            f"Gross ({result['grossAmount']}) != Net + VAT ({expected})"
        )
    return result


@app.get("/")
def health():
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/extract-invoice")
def extract_invoice(payload: InvoiceIn):
    if not payload.text or not payload.text.strip():
        return {"error": "empty text", "confidenceScore": 0,
                "anomalies": ["no text received"]}
    try:
        prompt = EXTRACTION_PROMPT.replace("{invoice_text}", payload.text)
        response = model.generate_content(prompt)
        data = _clean_json(response.text)
        cleaned = _clean_data(data)
        logger.info("Extracted invoice %s", cleaned.get("invoiceNumber"))
        return cleaned
    except json.JSONDecodeError:
        logger.exception("Model did not return valid JSON")
        return {"error": "invalid AI JSON", "confidenceScore": 0,
                "anomalies": ["AI response was not valid JSON"]}
    except Exception as exc:
        logger.exception("Extraction failed")
        return {"error": str(exc), "confidenceScore": 0,
                "anomalies": ["extraction failed"]}
