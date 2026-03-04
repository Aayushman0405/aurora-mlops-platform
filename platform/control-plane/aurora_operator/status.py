from kubernetes import client


def update_status(cr, phase):
    api = client.CustomObjectsApi()

    name = cr["metadata"]["name"]
    namespace = cr["metadata"]["namespace"]

    body = {
        "status": {
            "phase": phase
        }
    }

    api.patch_namespaced_custom_object_status(
        group="aurora.io",
        version="v1alpha1",
        namespace=namespace,
        plural="mltrainingjobs",
        name=name,
        body=body
    )

    print(f"🔄 Status updated to {phase}")
