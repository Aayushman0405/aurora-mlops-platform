from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pathlib import Path
import json
from api.security import api_key_auth

router = APIRouter(prefix="/models", tags=["models"])

ROOT = Path("/shared-models/aurora")

def resolve(model: str, ref: str) -> Path:
    base = ROOT / model

    if not base.exists():
        raise HTTPException(status_code=404, detail="Model not found")

    if ref.startswith("v"):
        path = base / "versions" / ref
    else:
        alias = base / "aliases" / ref
        if not alias.exists():
            raise HTTPException(status_code=404, detail="Alias not found")
        path = alias.resolve()

    if not path.exists():
        raise HTTPException(status_code=404, detail="Resolved path missing")

    return path

@router.get("/{model}/{ref}")
def metadata(
    model: str,
    ref: str,
    _=Depends(api_key_auth)
):
    path = resolve(model, ref)
    meta = path / "metadata.json"

    if not meta.exists():
        raise HTTPException(status_code=500, detail="Metadata missing")

    return json.loads(meta.read_text())

@router.get("/{model}/{ref}/artifact")
def artifact(
    model: str,
    ref: str,
    _=Depends(api_key_auth)
):
    path = resolve(model, ref)
    file = path / "model.pkl"

    if not file.exists():
        raise HTTPException(status_code=500, detail="Model artifact missing")

    return StreamingResponse(
        file.open("rb"),
        media_type="application/octet-stream"
    )

