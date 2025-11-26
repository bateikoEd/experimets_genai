from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="House QA Service")
app.include_router(router)


@app.get("/")
def root():
    return {"message": "House QA API running", "docs": "/docs"}
