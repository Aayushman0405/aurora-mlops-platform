import kopf
from kubernetes import client
from datetime import datetime

GROUP = "aurora.io"
VERSION = "v1alpha1"
PLURAL = "mldeployments"


def update_status(namespace, name, status):
    api = client.CustomObjectsApi()

    body = {
        "status": status
    }

    api.patch_namespaced_custom_object_status(
        group=GROUP,
        version=VERSION,
        namespace=namespace,
        plural=PLURAL,
        name=name,
        body=body,
    )


@kopf.on.create(GROUP, VERSION, PLURAL)
def on_create(spec, meta, namespace, **kwargs):
    name = meta["name"]

    print(f"🚀 MLDeployment created: {name}")

    status = {
        "phase": "Initializing",
        "stableVersion": "Production",
        "canaryVersion": "Staging",
        "decision": "Pending",
        "lastEvaluation": datetime.utcnow().isoformat(),
    }

    update_status(namespace, name, status)

    print(f"✅ MLDeployment {name} initialized")


@kopf.on.update(GROUP, VERSION, PLURAL)
def on_update(spec, meta, namespace, status, **kwargs):
    name = meta["name"]

    print(f"🔁 MLDeployment updated: {name}")

    new_status = status or {}
    new_status["lastEvaluation"] = datetime.utcnow().isoformat()

    update_status(namespace, name, new_status)

    print(f"🔄 MLDeployment {name} status refreshed")

