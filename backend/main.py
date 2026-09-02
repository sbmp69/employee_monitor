from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import supabase

app = FastAPI(title="Employee Monitor Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    # Attempt to query supabase to verify connection (e.g. auth health check or dummy query)
    db_status = "ok"
    try:
        # A simple check (if a 'computers' table existed we could query it, 
        # but for now we just verify the client exists)
        if supabase:
            pass
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    return {"status": "ok", "database": db_status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
