import os
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "Sunsine bot is alive ☀️"}

def run_web():
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
