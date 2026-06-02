from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


app = FastAPI(title="Travel Agent API", version="0.1.0")


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")
