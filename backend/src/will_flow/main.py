from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from will_flow.api.api_v1.api import api_router
from will_flow.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Flow Manager API",
    version="0.1.0",
)


    # Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Will Flow API", "docs_url": "/docs"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("will_flow.main:app", host="0.0.0.0", port=8000, reload=True) 