from fastapi import Request, HTTPException
import os

API_KEY = os.getenv("AURORA_API_KEY", "aurora-internal-key")

async def api_key_auth(request: Request):
    key = request.headers.get("x-api-key")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

