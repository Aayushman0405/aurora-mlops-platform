# Aurora MLOps Platform — Architecture

## Overview

Aurora is a production-style MLOps platform designed around **Kubernetes-native control**, **progressive delivery**, and **operational safety**.

The system separates:
- **Control** (what should happen)
- **Execution** (training, inference)
- **State** (models, artifacts)
- **Signals** (metrics, health)

This mirrors real-world ML platforms used at scale.

---

## High-Level Architecture


GitHub (GitOps)
|
v
Aurora Control Plane (FastAPI)
|
v
Aurora Operator (Kopf)
|
+--> Kubernetes Jobs (Training)
|
+--> Inference Deployments (Stable / Canary)



Storage and observability are shared primitives.

---

## Control Plane

**Component:** `aurora-control-plane`

**Responsibilities:**
- Platform APIs (`/health`, `/platform/info`)
- Cluster visibility (nodes, storage classes)
- Metrics exposure (Prometheus)
- Authentication via internal API key
- Optional controller bootstrap

**Key properties:**
- Stateless
- Horizontally scalable
- Does NOT run training or inference

This mirrors how real platforms avoid coupling control and execution.

---

## Operator Layer

**Component:** `aurora-operator` (Kopf-based)

**CRDs:**
- `MLTrainingJob`
- `MLDeployment`

**Responsibilities:**
- Watch custom resources
- Translate intent → Kubernetes primitives
- Create training Jobs
- Maintain status fields

The operator is **event-driven**, not cron-driven.

---

## Training Flow

1. User applies `MLTrainingJob`
2. Operator creates Kubernetes Job
3. Trainer writes model to shared RWX volume
4. Metadata and version are materialized
5. Status is updated on CRD

Training is **fully decoupled** from inference.

---

## Storage Design

**Primary storage:** CephFS (RWX)

**Why RWX matters:**
- Multiple pods read same model
- Zero-copy model promotion
- No object-store credentials in inference

**Layout (simplified):**
/models/
└── california-housing/
├── versions/
│ └── vYYYYMMDD-HHMMSS/
└── latest/


This avoids pulling models at runtime.

---

## Inference Layer

**Deployments:**
- `aurora-inference` (stable)
- `aurora-inference-canary`

**Characteristics:**
- Read-only model mount
- Startup validation via initContainer
- Readiness tied to model availability
- Explicit canary labeling

Inference pods never talk to MLflow or S3.

---

## Canary & Traffic Control

**Ingress:** NGINX

**Strategy:**
- Weight-based routing
- Separate services for stable/canary
- Same code, different labels

This enables:
- Safe production testing
- Side-by-side metric comparison
- Fast rollback

---

## Observability

**Metrics exposed:**
- Request count
- Latency histogram
- Error rate
- Model version label

**Why model version labels matter:**
You can answer:
> “Which model version caused the regression?”

This is often missing in toy projects.

---

## Design Principles

- GitOps as source of truth
- No runtime secrets in inference
- Fail-safe defaults
- Control ≠ execution
- Explicit versioning

---

## Phase Alignment

- Phase 1: Foundation ✅
- Phase 2: MLOps Core ✅
- Phase 3: Progressive Delivery ✅
- Phase 4: SRE & Chaos ⏳ (in progress)


