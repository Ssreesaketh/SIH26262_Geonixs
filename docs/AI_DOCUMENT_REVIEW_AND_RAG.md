# AI Document Review and Regulatory RAG

## What is implemented

- Authenticated `POST /api/v1/ai/documents/{document_id}/evaluate` for PDF-only advisory evaluation.
- Existing document access controls are checked before the file is read: institution users are tenant-scoped and regional officers are region-scoped.
- PyMuPDF extracts searchable PDF text; scanned pages can be OCR'd with Tesseract when the Python package and system binary are available.
- Processing has a configured maximum page count (`AI_MAX_PDF_PAGES`, default 60) and inherits the normal upload size limit.
- Reports persist in `document_evaluations` with evaluator, document/application/institution references, SHA-256 of the evaluated content, engine mode, and structured report JSON.
- `POST /api/v1/ai/knowledge/upload` indexes an administrator-curated PDF into page-aware `regulatory_chunks`; duplicate active file hashes are rejected.
- `POST /api/v1/ai/knowledge/{sha256}/deactivate` deactivates an old source without deleting historical evaluations or chunks.
- `POST /api/v1/ai/ask` retrieves only active curated regulatory chunks and returns source title, URL, version and page metadata.
- If Ollama and its configured LLM are available, it can generate source-grounded answers and structured review findings. If not, the API explicitly labels the result as retrieval-only or deterministic pre-check; it does not claim LLM evaluation occurred.
- If the configured Ollama embedding model is available, source chunks are embedded during indexing and cosine similarity is used for retrieval. Otherwise retrieval falls back to lexical ranking.
- New frontend navigation entry **Regulatory AI**, admin source curation, question UI, and per-PDF **AI review** action in Documents & forms.
- AI review is advisory. It never updates document verification state, approves/rejects an application, or advances a workflow.

## Configuration

Optional environment variables:

```dotenv
OLLAMA_URL=
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_EMBED_MODEL=nomic-embed-text
AI_MAX_PDF_PAGES=60
```

To use host-local Ollama from Docker Desktop on Windows, set `OLLAMA_URL=http://host.docker.internal:11434`, then pull both models on the host:

```powershell
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

Rebuild with `docker compose up --build`. Leave `OLLAMA_URL` empty to disable model calls. Do not configure an untrusted external endpoint. A model call may be slow on CPU-only systems.

## API summary

| Method | Path | Purpose | Access |
|---|---|---|---|
| POST | `/api/v1/ai/documents/{id}/evaluate` | Evaluate an authorized PDF and persist an advisory report | Authenticated, document access scoped |
| GET | `/api/v1/ai/documents/{id}/evaluations` | Read the last 20 reports for an authorized document | Authenticated, document access scoped |
| POST | `/api/v1/ai/knowledge/upload` | Index a verified regulatory PDF | System administrator only |
| GET | `/api/v1/ai/knowledge` | List active source metadata | Authenticated |
| POST | `/api/v1/ai/knowledge/{sha256}/deactivate` | Deactivate a source by its content hash | System administrator only |
| POST | `/api/v1/ai/ask` | Ask a source-grounded regulatory question | Authenticated |

## Important limitations

- The regulatory source catalogue must be populated with verified official documents by an authorized administrator. The application does not independently verify the authenticity or legal currency of a PDF.
- Vector embeddings are optional and are stored as JSON in PostgreSQL for this small prototype. For a larger corpus, use a versioned embedding pipeline and `pgvector` with index/migration support.
- The application does not currently include malware scanning, comprehensive PDF sanitization, automated legal interpretation, or a background queue for long model calls.
- OCR and model findings can be wrong. An authorized human must inspect the original document and cited source before recording any official outcome.
- Institution documents are not automatically indexed into the shared regulatory knowledge base. Cross-document institution analysis remains a later phase.
- This is a hackathon prototype, not an approved AICTE production service. Use synthetic data until privacy, security and legal reviews are complete.

## Verification status for this package

Source compilation, model/table creation, PDF extraction and advisory-fallback smoke checks were executed in the build environment. TypeScript type-checking passed. Full backend pytest execution was blocked in the build environment because the declared `bcrypt` dependency was not installed and network access was unavailable. Vite production build was blocked by a missing platform-specific Rollup optional dependency in the supplied `node_modules`; the Docker build performs a clean `npm install` and must be verified on the target machine. No Docker end-to-end run or real Ollama inference was claimed.
