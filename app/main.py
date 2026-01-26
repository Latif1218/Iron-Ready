from fastapi import FastAPI, status, HTTPException
from .database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get('/health', status_code=status.HTTP_200_OK)
def health():
    return HTTPException(
        status_code=status.HTTP_200_OK,
        detail="API is healthy and running correctly.",
        headers={"Iron_Ready Healthcheack": "healthy"}
    )