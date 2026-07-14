"""
bedrock_invoke.py
=================
Call a managed foundation model on **Amazon Bedrock** — the "no model ops" path.

WHY this file exists:
- Bedrock is the fastest way to get a strong LLM in production: you call an API and pay
  per token. No GPUs to provision, patch, or autoscale.
- This example shows the three things interviewers care about for managed inference:
    1) using an IAM role (NOT hardcoded keys) via the default credential chain,
    2) streaming responses for low time-to-first-token (better UX),
    3) where prompt caching / guardrails plug in to cut cost and add safety.

RUN (illustrative — needs AWS creds + Bedrock model access):
    pip install boto3
    export AWS_REGION=us-east-1
    python bedrock_invoke.py

NOTE: model IDs are illustrative; swap for a model you have access to.
"""

from __future__ import annotations

import json
import os

# boto3 is imported lazily inside functions so the file can be read/linted without the
# dependency installed. In real code, import at top-level.


# WHY the default credential chain: on AWS (EC2/EKS/Lambda) boto3 automatically picks up
# the attached IAM role's short-lived credentials. That means NO long-lived access keys
# in code, env files, or images — the single most common cloud security interview point.
def make_client(region: str | None = None):
    import boto3

    region = region or os.getenv("AWS_REGION", "us-east-1")
    # "bedrock-runtime" is the data-plane client used to actually invoke models.
    return boto3.client("bedrock-runtime", region_name=region)


def invoke_once(prompt: str, model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0") -> str:
    """Simple request/response. Good for batch or when you don't need streaming."""
    client = make_client()

    # The Converse API gives a provider-agnostic message shape across Bedrock models,
    # so you can swap Claude/Llama/Nova without rewriting the request body.
    response = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        # inferenceConfig controls cost/latency: fewer maxTokens = cheaper + faster.
        inferenceConfig={"maxTokens": 512, "temperature": 0.2},
    )
    return response["output"]["message"]["content"][0]["text"]


def invoke_stream(prompt: str, model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"):
    """
    Stream tokens as they are generated.

    WHY stream: time-to-first-token (TTFT) is what users feel. Streaming lets the UI show
    text immediately instead of waiting for the whole completion — critical for chat UX
    and a common latency question in interviews.
    """
    client = make_client()
    response = client.converse_stream(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 512, "temperature": 0.2},
    )
    for event in response["stream"]:
        # Each chunk carries a small delta of text; print without newline to stream.
        if "contentBlockDelta" in event:
            yield event["contentBlockDelta"]["delta"].get("text", "")


# --- Cost & safety hooks (where the money and risk actually live) --------------------
#
# PROMPT CACHING: for repeated long prefixes (a big system prompt or RAG context), Bedrock
# can cache the prefix so you don't pay to re-process it every call. This is one of the
# highest-ROI cost levers (often 30-50% savings). You mark cache points in the request.
#
# GUARDRAILS: attach a Bedrock Guardrail (guardrailIdentifier) to filter PII, block unsafe
# content, and defend against prompt injection — moves safety out of your app code.
#
# Both are added as extra parameters to converse()/converse_stream(); omitted here to keep
# the core call readable.


if __name__ == "__main__":
    demo_prompt = "In two sentences, explain why managed model APIs reduce ops burden."

    print("=== Single response ===")
    try:
        print(invoke_once(demo_prompt))
    except Exception as e:  # noqa: BLE001 - illustrative; real code handles specific errors
        print(f"(needs AWS creds + model access) {type(e).__name__}: {e}")

    print("\n=== Streaming response ===")
    try:
        for piece in invoke_stream(demo_prompt):
            print(piece, end="", flush=True)
        print()
    except Exception as e:  # noqa: BLE001
        print(f"(needs AWS creds + model access) {type(e).__name__}: {e}")
