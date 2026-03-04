from kubernetes import client
from kubernetes.client.rest import ApiException
import datetime

def create_training_job(cr):
    batch = client.BatchV1Api()

    name = cr["metadata"]["name"]
    namespace = cr["metadata"]["namespace"]
    spec = cr["spec"]

    job_name = f"train-{name}"
    
    # Generate version with timestamp
    version = datetime.datetime.utcnow().strftime("v%Y%m%d-%H%M%S")

    # 🔹 Trainer container
    container = client.V1Container(
        name="trainer",
        image="aayud/aurora-trainer:0.2.1",  # Make sure this has our updated code
        env=[
            client.V1EnvVar(name="MODEL_NAME", value=spec["modelName"]),
            client.V1EnvVar(name="ALGORITHM", value=spec["algorithm"]),
            client.V1EnvVar(name="MODEL_VERSION", value=version),
            # Add debugging
            client.V1EnvVar(name="PYTHONUNBUFFERED", value="1"),
        ],
        volume_mounts=[
            client.V1VolumeMount(
                name="model-volume",
                mount_path="/models",
            )
        ],
        # Add resource limits
        resources=client.V1ResourceRequirements(
            requests={"memory": "256Mi", "cpu": "250m"},
            limits={"memory": "512Mi", "cpu": "500m"}
        )
    )

    # 🔹 Pod spec with PVC
    pod_spec = client.V1PodSpec(
        restart_policy="Never",
        containers=[container],
        volumes=[
            client.V1Volume(
                name="model-volume",
                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                    claim_name="aurora-model-pvc"
                ),
            )
        ],
    )

    job = client.V1Job(
        metadata=client.V1ObjectMeta(name=job_name),
        spec=client.V1JobSpec(
            backoff_limit=1,
            ttl_seconds_after_finished=86400,  # Clean up after 24 hours
            template=client.V1PodTemplateSpec(
                spec=pod_spec
            ),
        ),
    )

    try:
        batch.create_namespaced_job(namespace=namespace, body=job)
        print(f"✅ Created training Job {job_name}")
        print(f"📝 Model: {spec['modelName']}, Version: {version}")
        
        # Wait a moment and check
        import time
        time.sleep(5)
        
        # Get job status
        print("⏳ Waiting for job to start...")
        
    except ApiException as e:
        if e.status == 409:
            print(f"⚠️ Job {job_name} already exists — skipping")
        else:
            print(f"❌ Failed to create job: {e}")
            raise
