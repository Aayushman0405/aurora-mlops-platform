# Aurora — Kubernetes-Native ML Platform

Aurora is a production-grade, Kubernetes-native Machine Learning platform that manages the complete ML lifecycle:
training, versioning, deployment, and inference — with built-in support for canary rollouts and observability.

This project is inspired by internal ML platforms used at large tech companies.

---

## Features

- 🧠 ML training orchestration via CRDs
- 📦 Versioned model registry on CephFS (RWX)
- 🚀 Dynamic model serving (no rebuilds)
- 🟡 Canary + Stable deployments
- ⚖️ Traffic splitting using NGINX Ingress
- 🔐 API-secured internal communication
- 📊 Prometheus metrics everywhere
- 🔁 GitOps-driven deployment

---

## Core Components

| Component     | Description                               |
|---------------|-------------------------------------------|
| Control Plane | FastAPI service for models & cluster APIs |
| Operator      | Kopf-based Kubernetes operator            |
| Trainer       | Containerized ML training runtime         |
| Inference     | Stateless prediction service              |
| Storage       | CephFS RWX shared volume                  |
| GitOps        | Kubernetes manifests as source of truth   |

---

## Custom Resources

### MLTrainingJob

```yaml
apiVersion: aurora.io/v1alpha1
kind: MLTrainingJob
spec:
  modelName: california-housing


Triggers a Kubernetes Job that trains and stores a new model version.


MLDeployment
apiVersion: aurora.io/v1alpha1
kind: MLDeployment
spec:
  modelName: california-housing
  strategy:
    type: Canary
    canaryWeight: 10

Defines rollout strategy and deployment intent.


Model Serving Flow

Training job writes model to shared storage
Control Plane exposes metadata + artifacts
Inference runtime fetches model on startup
NGINX routes traffic between stable & canary
Metrics collected for evaluation


Security

API-key based internal auth
Namespace-scoped RBAC
No public access to model artifacts
Observability

Prometheus metrics for:
Requests
Latency
Errors
Model versions
Ready for Grafana dashboards

  dataset: synthetic
  algorithm: random_forest
