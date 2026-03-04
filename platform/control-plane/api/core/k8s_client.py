from kubernetes import client, config

def load_kube_config():
    try:
        config.load_incluster_config()
    except Exception:
        config.load_kube_config()

load_kube_config()

core_v1 = client.CoreV1Api()
storage_v1 = client.StorageV1Api()
