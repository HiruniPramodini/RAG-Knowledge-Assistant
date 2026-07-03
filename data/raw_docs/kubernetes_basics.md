# Kubernetes Fundamentals

## What is Kubernetes?

Kubernetes (often abbreviated K8s) is an open-source system for automating the deployment, scaling, and management of containerized applications. While Docker packages and runs individual containers, Kubernetes orchestrates many containers across a cluster of machines, handling tasks like restarting failed containers, distributing traffic between them, and scaling the number of running instances up or down based on demand.

## Why Use Kubernetes Instead of Just Docker?

Running a single container with `docker run` works fine for local development, but production systems typically need multiple copies of an application running for reliability, automatic recovery when something crashes, load balancing across those copies, and the ability to scale up during high traffic and scale down during low traffic. Kubernetes automates all of this, which becomes essential once an application needs to run reliably at scale rather than as a single instance on a single machine.

## Core Concepts

**Pod** — the smallest deployable unit in Kubernetes. A pod wraps one or more containers that share networking and storage, and are always scheduled together on the same machine. Most commonly, a pod contains a single container.

**Node** — a physical or virtual machine in the Kubernetes cluster that runs pods. A cluster typically has multiple nodes, and Kubernetes decides which node runs which pod based on available resources.

**Deployment** — a higher-level object that manages a set of identical pods, ensuring a specified number of replicas are always running. If a pod crashes, the Deployment automatically creates a replacement. Deployments also manage rolling updates, gradually replacing old pod versions with new ones without downtime.

**Service** — provides a stable network address for a set of pods, even as individual pods are created and destroyed. Since pods are ephemeral and get new IP addresses when recreated, a Service acts as a consistent entry point that routes traffic to whichever pods are currently healthy and running.

**ConfigMap and Secret** — ConfigMaps store non-sensitive configuration data (like environment variable values) separately from application code, so configuration can change without rebuilding the container image. Secrets work similarly but are intended for sensitive data like API keys and passwords, with additional access controls.

## Scaling

Kubernetes supports both manual and automatic scaling. Horizontal Pod Autoscaling (HPA) automatically increases or decreases the number of running pod replicas based on observed metrics such as CPU utilization or custom metrics like request latency. This means a system can automatically add more instances of a model-serving API during a traffic spike and scale back down afterward, without a human manually intervening.

## Rolling Updates and Rollbacks

When deploying a new version of an application, Kubernetes can perform a rolling update: it gradually replaces old pods with new ones a few at a time, checking that new pods are healthy before continuing, rather than shutting down all old instances at once. If the new version turns out to be broken, Kubernetes supports rolling back to the previous known-good version, which is directly analogous to the model rollback concept used in MLOps when a newly deployed model underperforms in production.

## Kubernetes and MLOps

In machine learning infrastructure, Kubernetes is commonly used to run model-serving APIs at scale, ensuring multiple replicas of a model server are always available, automatically restarting them if they crash, and scaling them based on incoming prediction request volume. It also underlies platforms like Kubeflow, which build ML-specific pipeline orchestration on top of Kubernetes primitives.
