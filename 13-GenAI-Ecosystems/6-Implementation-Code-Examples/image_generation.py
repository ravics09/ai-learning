"""
image_generation.py
====================
WHY THIS FILE:
    Shows the IMAGE modality of the ecosystem. Two paths, two trade-offs:
        (A) API diffusion (OpenAI Images) — zero infra, fast to ship, per-image cost, data
            leaves your boundary.
        (B) Local diffusion (Stable Diffusion / FLUX via `diffusers`) — full control, no
            per-image fee, privacy, custom LoRA styles, but needs a capable GPU.
    This mirrors the closed-vs-open trade-off, applied to images instead of text.

SETUP:
    pip install openai            # for path A
    export OPENAI_API_KEY=...
    # path B (optional, heavy):  pip install diffusers torch transformers accelerate

RUN:
    python image_generation.py
"""

from __future__ import annotations

import base64
import os


def generate_via_api(prompt: str, out_path: str = "api_image.png") -> str:
    """Path A: generate an image through a hosted diffusion API.

    WHY: fastest way to add image generation — no GPU, no model download. Good default
    until volume/privacy pushes you to self-host.
    """
    from openai import OpenAI

    client = OpenAI()
    result = client.images.generate(
        model="gpt-image-1",   # hosted image model
        prompt=prompt,
        size="1024x1024",
    )
    # The API returns base64; decode and save it.
    image_b64 = result.data[0].b64_json
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(image_b64))
    return out_path


def generate_locally(prompt: str, out_path: str = "local_image.png") -> str:
    """Path B: run a diffusion model on your own GPU.

    WHY: control + privacy + no per-image cost. Key knobs explained below because they are
    the classic quality/latency trade-off for diffusion models.
    """
    import torch  # noqa: F401  (import here so path A works without torch installed)
    from diffusers import StableDiffusionPipeline

    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16,  # fp16 halves VRAM with negligible quality loss
    ).to("cuda")

    image = pipe(
        prompt,
        num_inference_steps=30,   # MORE steps = better quality but higher latency/cost
        guidance_scale=7.5,       # CFG: how strongly the image follows the prompt
        # negative_prompt="blurry, low quality",  # steer AWAY from artifacts
    ).images[0]

    image.save(out_path)
    return out_path


if __name__ == "__main__":
    prompt = "a minimalist isometric illustration of a data center, soft pastel colors"

    print("[A] API diffusion (no infra):")
    if os.getenv("OPENAI_API_KEY"):
        try:
            path = generate_via_api(prompt)
            print(f"  saved -> {path}")
        except Exception as e:  # noqa: BLE001
            print(f"  API generation failed: {e}")
    else:
        print("  Set OPENAI_API_KEY to try the API path.")

    print("\n[B] Local diffusion (control + privacy, needs GPU):")
    try:
        path = generate_locally(prompt)
        print(f"  saved -> {path}")
    except Exception as e:  # noqa: BLE001
        print(f"  Local path skipped (needs diffusers + CUDA GPU): {e}")
