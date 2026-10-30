import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api.api_v1 import api_router
from app.seed_data import seed_database
from app.services.sla_engine import SLAEngine
from sqlalchemy import inspect, text

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist
    Base.metadata.create_all(bind=engine)
    # Lightweight additive migration for databases created by earlier demo versions.
    # No existing document records or files are deleted.
    inspector = inspect(engine)
    if "documents" in inspector.get_table_names():
        existing_columns = {column["name"] for column in inspector.get_columns("documents")}
        if "verification_remarks" not in existing_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE documents ADD COLUMN verification_remarks TEXT NULL"))
    
    # Ensure seeded demonstration documents are valid, readable PDFs. Older builds
    # wrote a tiny placeholder that a PDF parser cannot open; replace only that exact
    # known placeholder, never overwrite a real uploaded document.
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    sample_files = [
        ("sample_lease_deed_nit402.pdf", "Synthetic lease evidence — NIT-402", "DEMONSTRATION ONLY. This is fabricated sample content, not a legal deed or official evidence."),
        ("sample_fire_noc_zen801.pdf", "Synthetic fire NOC evidence — ZEN-801", "DEMONSTRATION ONLY. This is fabricated sample content, not a government-issued NOC."),
    ]
    for sf, title, body in sample_files:
        sample_path = os.path.join(settings.STORAGE_DIR, sf)
        should_create = not os.path.exists(sample_path)
        if not should_create:
            try:
                with open(sample_path, "rb") as existing_file:
                    existing_bytes = existing_file.read(512)
                should_create = b"Synthetic Sample Document Placeholder" in existing_bytes
            except OSError:
                should_create = False
        if should_create:
            try:
                import fitz
                sample_pdf = fitz.open()
                page = sample_pdf.new_page()
                page.insert_text((72, 72), title, fontsize=16)
                page.insert_textbox(fitz.Rect(72, 110, 520, 240), body, fontsize=11)
                page.insert_text((72, 280), "SIH26262 synthetic demonstration record", fontsize=9)
                sample_pdf.save(sample_path)
                sample_pdf.close()
            except Exception:
                # Keep startup available if a PDF writer fails; the evaluator will
                # return a clear parse error rather than treating this as verified evidence.
                with open(sample_path, "wb") as f:
                    f.write(b"%PDF-1.4\n%SIH26262 Synthetic Sample Document Placeholder\n%%EOF")

    # Seed initial demonstration database
    db = SessionLocal()
    try:
        seed_database(db, reset=False)
        # Run initial SLA evaluation to prepare demonstration alerts
        SLAEngine.evaluate_all(db)
    finally:
        db.close()

    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

@app.middleware("http")
async def enforce_upload_content_length(request: Request, call_next):
    """Reject oversized upload requests before multipart parsing when length is known."""
    is_upload = request.url.path.endswith("/documents/upload") or ("/documents/" in request.url.path and request.url.path.endswith("/renew"))
    if request.method == "POST" and is_upload:
        raw_length = request.headers.get("content-length")
        if raw_length:
            try:
                request_size = int(raw_length)
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length header"})
            # Allow 1 MiB for multipart boundaries and form fields in addition to the file cap.
            if request_size > settings.MAX_FILE_SIZE_BYTES + 1024 * 1024:
                return JSONResponse(status_code=413, content={"detail": f"Upload request exceeds the {settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB file limit plus form overhead."})
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("X-Frame-Options", "DENY")
    return response

# CORS Middleware (strict local origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global safe error handling
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log internal error safely without exposing stack traces in production
    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal administrative service error occurred. Please contact AICTE support."}
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)}
    )

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT
    }

app.include_router(api_router, prefix=settings.API_V1_STR)
