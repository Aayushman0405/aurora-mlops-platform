from kubernetes import client, watch, config
from aurora_operator.training_job import create_training_job
from aurora_operator.status import update_status

GROUP = "aurora.io"
VERSION = "v1alpha1"
PLURAL = "mltrainingjobs"

NAMESPACE = "aurora-system"

def run_controller():
    try:
        config.load_incluster_config()
        print("✅ Loaded in-cluster Kubernetes config")
    except Exception as e:
        print(f"❌ Failed to load in-cluster config: {e}")
        return

    api = client.CustomObjectsApi()
    w = watch.Watch()

    print("🚀 AURORA MLTrainingJob controller started")

    for event in w.stream(
        api.list_namespaced_custom_object,
        group=GROUP,
        version=VERSION,
        namespace=NAMESPACE,
        plural=PLURAL,
        timeout_seconds=0,
    ):
        obj = event["object"]
        event_type = event["type"]

        name = obj["metadata"]["name"]
        print(f"📡 Event {event_type} for MLTrainingJob {name}")

        if event_type == "ADDED":
            print(f"📌 New MLTrainingJob detected: {name}")
            create_training_job(obj)
            update_status(obj, phase="Running")

