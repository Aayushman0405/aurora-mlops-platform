# Aurora ML Platform — Architecture

## Overview

Aurora is a Kubernetes-native Machine Learning platform designed to manage the full ML lifecycle:
training, versioning, deployment, and inference — with safe rollout strategies such as canary deployments.

The platform follows **control-plane / data-plane separation**, GitOps principles, and cloud-native observability.

---

## High-Level Architecture

┌──────────────┐
│ GitHub Repo │
└──────┬───────┘
       │ CI/CD
       ▼
┌────────────────────────┐
│ GitHub Actions         │
│ (Self-Hosted Runner)   │
└────────┬───────────────┘
         │ kubectl apply
         ▼
┌────────────────────────────────────────────┐
│       Kubernetes Cluster                   │
│                                            │
│ ┌──────────────┐      ┌─────────────────┐  │
│ │ Aurora       │      │ Aurora Operator │  │
│ │ ControlPlane │◀───▶│ (Kopf)          │  │
│ └──────┬───────┘      └──────┬──────────┘  │
│        │ REST API            │ CRDs        │
│        ▼                     ▼             │
│ ┌──────────────┐        ┌────────────────┐ │ 
│ │ Inference    │◀───── │ MLTrainingJob   │ │
│ │ Runtime      │        │ MLDeployment   │ │
│ └──────────────┘        └────────────────┘ │
│    │                                       │
│    ▼                                       │
│ ┌──────────────────────────────────────┐   │
│ │ CephFS (RWX Shared Model Storage)    │   │
│ └──────────────────────────────────────┘   │
│                                            │
└────────────────────────────────────────────┘


---

## Core Components

### 1. Aurora Control Plane

**Technology:** FastAPI  
**Responsibilities:**
- Serve model metadata and artifacts
- Provide cluster & storage introspection
- Enforce API-key authentication
- Expose Prometheus metrics

**Key APIs:**
- `/models/{model}/{ref}`
- `/models/{model}/{ref}/artifact`
- `/cluster/nodes`
- `/storage/classes`
- `/metrics`

Mounted with **RWX CephFS** at `/shared-models`.

---

### 2. Model Storage Layer

**Storage Type:** CephFS (ReadWriteMany)  
**PVC:** `aurora-model-pvc`

**Directory Layout**
/shared-models/aurora/
├── registry/
│ ├── current-version
│ └── metadata.json
├── california-housing/
│ ├── versions/
│ │ └── vYYYYMMDD-HHMMSS/
│ │ ├── model.pkl
│ │ └── metadata.json
│ └── aliases/
│ ├── stable -> versions/vX
│ └── canary -> versions/vY



Initialized via a Kubernetes Job.

---

### 3. Aurora Operator

**Framework:** Kopf  
**CRDs Managed:**
- `MLTrainingJob`
- `MLDeployment`

#### MLTrainingJob Flow
1. CR created
2. Operator spawns Kubernetes Job
3. Trainer container:
   - Trains model
   - Writes artifact + metadata to CephFS
4. Status updated

#### MLDeployment Flow
- Tracks rollout intent
- Stores canary/stable metadata
- Ready for automated promotion logic

---

### 4. Training Runtime

**Containerized Trainer**
- Uses scikit-learn
- Version generated via timestamp
- Writes directly to shared model store
- Fully decoupled from inference

---

### 5. Inference Runtime

**Design Highlights**
- Stateless containers
- Fetch models at startup
- Cache locally
- No rebuild required for promotion

**Deployment Types**
- Stable deployment (replicas = 3)
- Canary deployment (replicas = 1)

**Traffic Splitting**
- NGINX Ingress canary annotations
- Weight-based routing

---

### 6. Observability

**Metrics**
- Request count
- Latency histograms
- Error counters
- Model loaded gauge

**Scraped by Prometheus** via annotations.

---

## Design Principles

- Kubernetes-native first
- API-driven ML lifecycle
- Storage-backed model registry
- GitOps as source of truth
- Safe rollout via canaries
- Zero-downtime inference updates

---

## Future Extensions

- Automated canary evaluation
- SLO-based promotion
- Model lineage tracking
- Drift detection
- Cost-aware scaling


