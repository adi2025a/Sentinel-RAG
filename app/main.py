from fastapi import FastAPI, UploadFile, File, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
from tests.rag_test import ingestion_test , query_test


app = FastAPI()

# --- Simple admin authentication dependency ---
def admin_auth(token: str = Query(..., description="Admin token")):
    ADMIN_TOKEN = "supersecret"  # Replace with env variable or config
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Not authorized")
    return True

# --- Admin route: Upload PDF ---
@app.post("/admin/upload-pdf/")
async def upload_pdf(
    file: UploadFile = File(...),
    authorized: bool = Depends(admin_auth)
):
    contents = await file.read()
    ingestion_test(contents)
    return JSONResponse(content={
        "filename": file.filename,
        "content_type": file.content_type,
        "message": f"Admin uploaded PDF '{file.filename}' successfully"
    })

# --- Public route: User query ---
@app.get("/user/query/")
async def user_query(query: str = Query(..., description="User query string")):
    # For demo, just echo the query back
    answer = query_test(query)
    response = {
        "query": query,
        "answer": answer
    }
    return JSONResponse(content=response)
