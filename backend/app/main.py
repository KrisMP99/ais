from fastapi import FastAPI
import importlib

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}