from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Travel API", version="0.1.0")


class HealthResponse(BaseModel):
    status: str


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")
