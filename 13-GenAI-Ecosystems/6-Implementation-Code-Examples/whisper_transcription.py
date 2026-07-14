"""
whisper_transcription.py
========================
WHY THIS FILE:
    Covers the AUDIO -> TEXT (STT/ASR) modality. Whisper is the de-facto open-weight speech
    model: robust, multilingual, and free to self-host. Here we use `faster-whisper`
    (a CTranslate2 reimplementation) because it runs several times faster than the reference
    model and supports int8 quantization on CPU — a concrete example of quantization making
    a model practical on modest hardware.

    Use case: transcribe a voice note in a support ticket, then feed the transcript into an
    LLM (see the multimodal pipeline diagram) — audio becomes just another text input.

SETUP:
    pip install faster-whisper
    # Provide any audio file (wav/mp3/m4a). ffmpeg is used under the hood.

RUN:
    python whisper_transcription.py path/to/audio.mp3
"""

from __future__ import annotations

import sys

from faster_whisper import WhisperModel


def transcribe(audio_path: str, model_size: str = "base") -> None:
    """Transcribe an audio file to text with timestamps.

    model_size trade-off (WHY it matters):
        tiny/base  -> fast, low memory, lower accuracy  (great for drafts / edge)
        small/medium -> balanced
        large-v3   -> best accuracy, slowest, most memory
    Pick the smallest size that clears your accuracy bar — the same right-sizing logic we
    apply to LLMs.
    """
    # compute_type="int8" quantizes weights to 8-bit so it runs well on CPU.
    # On a GPU you'd use device="cuda", compute_type="float16".
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    # `segments` is a lazy generator — transcription streams as it decodes.
    segments, info = model.transcribe(audio_path, beam_size=5)

    print(f"Detected language: {info.language} (p={info.language_probability:.2f})")
    print("-" * 60)

    full_text: list[str] = []
    for seg in segments:
        # Timestamps are useful for captions, search, and aligning to the source audio.
        print(f"[{seg.start:6.2f}s -> {seg.end:6.2f}s] {seg.text.strip()}")
        full_text.append(seg.text.strip())

    print("-" * 60)
    print("FULL TRANSCRIPT:\n" + " ".join(full_text))
    # In a real pipeline you'd now pass this transcript to an LLM for summarization/routing.


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python whisper_transcription.py <audio-file>")
        print("Tip: any short .mp3/.wav works. Larger model sizes = higher accuracy.")
        sys.exit(0)

    try:
        transcribe(sys.argv[1])
    except Exception as e:  # noqa: BLE001
        print(f"Transcription failed: {e}")
        print("Check the file path and that ffmpeg is installed.")
