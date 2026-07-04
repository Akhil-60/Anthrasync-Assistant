"""
api.py  -  the FastAPI interface (assignment's "API" requirement).

Exposes:
- POST /ask (Round 1: RAG question answering)
- POST /extract-invoice (Round 3 Task 1: Invoice extraction for n8n)

Run with:
    uvicorn src.api:app --reload
"""

from fastapi import FastAPI
from pydantic import BaseModel

from src.pipeline import RAGPipeline

app = FastAPI(title="Anthrasync Enterprise Knowledge Assistant API")

pipeline = RAGPipeline()


# ==================== ROUND 1: EXISTING MODELS & ENDPOINTS ====================

class AskRequest(BaseModel):
    question: str


class Source(BaseModel):
    document: str
    page: int


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    confidence: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    return pipeline.ask(request.question)


# ==================== ROUND 3 TASK 1: INVOICE EXTRACTION ====================

class InvoiceExtractRequest(BaseModel):
    text: str  # <--- YAHAN "text" HI HAI, "message" NAHI


class InvoiceExtractResponse(BaseModel):
    vendor: str | None
    vendorUid: str | None
    vendorIban: str | None
    invoiceNumber: str | None
    invoiceDate: str | None
    dueDate: str | None
    netAmount: float
    vatAmount: float
    vatPercentage: float
    grossAmount: float
    currency: str | None
    costCenter: str | None
    lineItems: list
    confidenceScore: float
    anomalies: list


@app.post("/extract-invoice", response_model=InvoiceExtractResponse)
def extract_invoice(request: InvoiceExtractRequest):
    """
    Endpoint for n8n to call. Takes raw invoice text, returns structured JSON.
    """
    try:
        result = pipeline.generator.extract_invoice_data(request.text)
        
        # Safety net - ensure all fields exist
        result.setdefault("vendor", None)
        result.setdefault("vendorUid", None)
        result.setdefault("vendorIban", None)
        result.setdefault("invoiceNumber", None)
        result.setdefault("invoiceDate", None)
        result.setdefault("dueDate", None)
        result.setdefault("netAmount", 0.0)
        result.setdefault("vatAmount", 0.0)
        result.setdefault("vatPercentage", 0.0)
        result.setdefault("grossAmount", 0.0)
        result.setdefault("currency", None)
        result.setdefault("costCenter", None)
        result.setdefault("lineItems", [])
        result.setdefault("confidenceScore", 0.0)
        result.setdefault("anomalies", [])
        
        return result
    except Exception as e:
        return {
            "vendor": None,
            "vendorUid": None,
            "vendorIban": None,
            "invoiceNumber": f"ERROR: {str(e)}",
            "invoiceDate": None,
            "dueDate": None,
            "netAmount": 0.0,
            "vatAmount": 0.0,
            "vatPercentage": 0.0,
            "grossAmount": 0.0,
            "currency": None,
            "costCenter": None,
            "lineItems": [],
            "confidenceScore": 0.0,
            "anomalies": ["Internal server error, check logs"]
        }