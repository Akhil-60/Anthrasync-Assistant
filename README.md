# AI Invoice Automation Workflow

**Round 3 · Task 1 — AI Engineer Assignment**

An end-to-end, AI-powered invoice processing pipeline. Invoices arrive by email as PDF attachments; the system reads them, extracts structured data using an LLM, stores a clean record in a database, and routes each invoice through a human approval step.

## Overview
Two n8n workflows backed by a FastAPI + Gemini microservice and Airtable database.

- **Workflow 1 — Ingestion:** Gmail Trigger -> IF (PDF filter) -> Extract from PDF -> HTTP Request (FastAPI /extract-invoice) -> Code (clean JSON) -> Airtable (Status = Draft)
- **Workflow 2 — Approval:** Trigger -> Airtable Search (Send for Approval = true AND Status = Draft) -> Gmail notify -> human sets Status Fully Approved/Rejected + Approved At

## Tech Stack
- Orchestration: n8n (Docker)
- AI/LLM: Google Gemini (gemini-2.5-flash-lite) via google-generativeai
- Backend: FastAPI + Python (no LangChain)
- Database: Airtable
- Email: Gmail (OAuth2 via n8n)

## Environment Variables
Create a .env file:
GEMINI_API_KEY=your_key_here

Gmail (OAuth2) and Airtable (Personal Access Token) credentials are configured inside n8n.

## Setup
1. python -m venv venv ; venv\Scripts\activate ; pip install -r requirements.txt
2. Add GEMINI_API_KEY to .env
3. Start API: uvicorn invoice_api:app --host 0.0.0.0 --port 8000 --reload
4. Start n8n: docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n:latest
5. Open n8n at http://127.0.0.1:5678 (use 127.0.0.1, not localhost, on Windows)
6. Import both workflow JSONs from n8n-workflows/
7. Configure Gmail + Airtable credentials in n8n
8. Activate the Ingestion workflow

## Workflow Explanation
Ingestion: detects PDF-attachment emails, ignores non-PDF (IF false branch empty), extracts text, sends to Gemini via FastAPI, cleans the JSON, and creates a Draft record.
Approval: finds invoices flagged for approval, emails the approver a summary; approver updates status in Airtable with an Approved At timestamp (audit trail).

## AI Prompt
The FastAPI service prompts Gemini to return valid JSON only, with fields: vendor, vendorUid, vendorIban, invoiceNumber, invoiceDate, dueDate, netAmount, vatAmount, vatPercentage, grossAmount, currency, costCenter, lineItems[], confidenceScore, anomalies[]. Numbers as numbers, dates as YYYY-MM-DD, nulls where missing. (Exact prompt in src/generator.py.)

## Error Handling
- Non-PDF emails filtered by IF node.
- FastAPI applies safe defaults to every field; on error returns valid JSON with the error in anomalies.
- Empty line items removed; confidence + anomalies stored for review.

## Assumptions
- Approval via manual Airtable status update (reliable); production can use n8n Send-and-Wait for email-button approval.
- PDF stored via Airtable attachment; production uploads to object storage and stores the URL.
- Single attachment per email assumed.
- Use 127.0.0.1 / host.docker.internal on Windows.

## Security
Secrets live only in .env (git-ignored) and n8n credentials. Regenerate any exposed key/token.
