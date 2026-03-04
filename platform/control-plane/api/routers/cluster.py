from fastapi import APIRouter
from api.core.k8s_client import core_v1

router = APIRouter()

@router.get("/cluster/nodes")
def list_nodes():
    nodes = core_v1.list_node()
    return [
        {
            "name": node.metadata.name,
            "status": node.status.conditions[-1].type
        }
        for node in nodes.items
    ]
