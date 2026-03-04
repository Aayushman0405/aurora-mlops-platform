import kopf
from kubernetes import config
import aurora_operator.deployment_controller
from aurora_operator.training_job import create_training_job

config.load_incluster_config()

@kopf.on.create("aurora.io", "v1alpha1", "mltrainingjobs")
def on_create(spec, meta, namespace, **kwargs):
    cr = {
        "metadata": {
            "name": meta["name"],
            "namespace": namespace,
        },
        "spec": spec,
    }

    print(f"🚀 MLTrainingJob detected: {meta['name']}")
    create_training_job(cr)

