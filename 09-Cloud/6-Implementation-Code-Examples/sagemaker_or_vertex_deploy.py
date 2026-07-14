"""
sagemaker_or_vertex_deploy.py
=============================
Deploy YOUR OWN model to a managed endpoint — the "control without a cluster" path.

WHY this file exists:
- Managed FM APIs (Bedrock) are great, but sometimes you need a custom / fine-tuned /
  open-weight model. SageMaker (AWS) and Vertex AI (GCP) let you deploy your own model
  behind an autoscaling HTTPS endpoint WITHOUT running Kubernetes yourself.
- This shows the two big interview points for managed custom deployment:
    1) point the endpoint at model artifacts in OBJECT STORAGE (S3/GCS) — the source of
       truth you can version and replicate for DR,
    2) turn on AUTOSCALING (incl. scale-to-zero on serverless) so you don't pay for idle.

Both providers are shown side by side so you can compare the mental model. Code is
illustrative pseudo-config (SDK calls sketched) — swap in real ARNs/URIs/project IDs.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# AWS SageMaker: real-time endpoint with autoscaling
# ---------------------------------------------------------------------------
def deploy_sagemaker():
    """
    Steps (using the SageMaker Python SDK):

      1. Model artifacts live in S3 (model.tar.gz). WHY: object storage is durable,
         versioned, cross-region-replicable -> your DR + rollback story.
      2. Create a Model from a container image (e.g., a vLLM/DJL/HF inference image) +
         the S3 artifact.
      3. Deploy to an endpoint on a GPU instance (e.g., ml.g5.xlarge = cost-efficient L4-class).
      4. Attach Application Auto Scaling so replicas track load instead of being fixed.
    """
    from sagemaker.model import Model  # type: ignore
    from sagemaker import image_uris  # type: ignore

    image = image_uris.retrieve(framework="djl-lmi", region="us-east-1", version="latest")

    model = Model(
        image_uri=image,
        model_data="s3://my-models/llama-3-8b/model.tar.gz",  # versioned artifact
        role="arn:aws:iam::123456789012:role/SageMakerExecRole",  # least-privilege role
    )

    predictor = model.deploy(
        initial_instance_count=1,
        instance_type="ml.g5.xlarge",          # GPU right-sized for an 8B model
        endpoint_name="llama3-8b-endpoint",
    )

    # WHY autoscaling: fixed capacity either wastes money (over-provisioned) or drops
    # requests (under-provisioned). Scale on invocations-per-instance, a real load signal.
    #   import boto3
    #   aas = boto3.client("application-autoscaling")
    #   aas.register_scalable_target(... MinCapacity=1, MaxCapacity=8 ...)
    #   aas.put_scaling_policy(TargetValue=<invocations/instance>, ...)

    # TIP: for spiky/low volume, use SageMaker *Serverless Inference* instead -> scales to
    # zero (pay per request). Trade-off: cold starts while a worker spins up.
    return predictor


# ---------------------------------------------------------------------------
# GCP Vertex AI: upload model -> create endpoint -> deploy with autoscaling
# ---------------------------------------------------------------------------
def deploy_vertex():
    """
    Steps (using google-cloud-aiplatform):

      1. Artifacts live in GCS (gs://...). Same DR/versioning benefit as S3.
      2. Upload as a Vertex Model (with a serving container).
      3. Create an Endpoint and deploy the model to it on a GPU machine type.
      4. Set min/max replicas -> autoscaling. Vertex scales on utilization.
    """
    from google.cloud import aiplatform  # type: ignore

    aiplatform.init(project="my-project", location="us-central1")

    model = aiplatform.Model.upload(
        display_name="llama3-8b",
        artifact_uri="gs://my-models/llama-3-8b/",       # versioned artifact in GCS
        serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/vllm:latest",
    )

    endpoint = model.deploy(
        machine_type="g2-standard-8",                    # L4 GPU machine (cost-efficient)
        accelerator_type="NVIDIA_L4",
        accelerator_count=1,
        min_replica_count=1,                             # set 0-friendly patterns via
        max_replica_count=8,                             # dedicated serverless if needed
        traffic_split={"0": 100},                        # 100% to this version (canary-able)
    )
    return endpoint


# ---------------------------------------------------------------------------
# Interview takeaway
# ---------------------------------------------------------------------------
# SageMaker vs Vertex are conceptually identical here:
#   artifact in object storage  ->  container image  ->  autoscaling GPU endpoint.
# Pick based on the cloud you're already in and the models/tooling you need.
# Use these when you need a CUSTOM model but DON'T want to run Kubernetes yourself.
# Move to EKS/GKE + vLLM (see k8s_llm_deployment.yaml) only when you need max control
# and utilization at high, steady volume.

if __name__ == "__main__":
    print("This is an illustrative deployment sketch — see comments for the real SDK flow.")
    print("SageMaker path: deploy_sagemaker()  |  Vertex path: deploy_vertex()")
