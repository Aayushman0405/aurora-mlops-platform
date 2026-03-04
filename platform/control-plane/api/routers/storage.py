from fastapi import APIRouter
from api.core.k8s_client import storage_v1

router = APIRouter()

@router.get("/storage/classes")
def list_storage_classes():
    scs = storage_v1.list_storage_class()
    return [
        {
            "name": sc.metadata.name,
            "provisioner": sc.provisioner,
            "reclaimPolicy": sc.reclaim_policy
        }
        for sc in scs.items
    ]
