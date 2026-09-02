from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import supabase
from routers import agent, admin, stream

app = FastAPI(title="Employee Monitor Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(stream.router, prefix="/api", tags=["stream"])

@app.get("/health")
def health_check():
    db_status = "ok"
    try:
        if supabase:
            pass
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    return {"status": "ok", "database": db_status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
