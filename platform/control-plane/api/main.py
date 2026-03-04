from fastapi import FastAPI, Depends
from api.routers import health, platform, storage, cluster, models
from api.security import api_key_auth

app = FastAPI(title="Aurora Control Plane", version="1.0")

# --------------------
# Public routes
# --------------------
app.include_router(health.router)

# --------------------
# Protected routes
# --------------------
app.include_router(platform.router, dependencies=[Depends(api_key_auth)])
app.include_router(storage.router, dependencies=[Depends(api_key_auth)])
app.include_router(cluster.router, dependencies=[Depends(api_key_auth)])
app.include_router(models.router, dependencies=[Depends(api_key_auth)])

