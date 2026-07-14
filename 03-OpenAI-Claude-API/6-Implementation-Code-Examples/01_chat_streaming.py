"""
01_chat_streaming.py
====================
Stream a chat completion token-by-token over Server-Sent Events (SSE) for
both OpenAI and Anthropic Claude.

WHY STREAM?
-----------
Generation is sequential (each output token depends on the previous one), so a
non-streaming call makes the user wait for the ENTIRE response before seeing
anything. Streaming emits tokens as they are produced, collapsing the
*perceived* latency: time-to-first-token (TTFT) drops from seconds to a few
hundred milliseconds. This is almost always the right default for interactive
UIs (chatbots, assistants).

WHAT TO WATCH FOR
-----------------
- You lose the single `usage` object when streaming, so you must explicitly ask
  for it (OpenAI: stream_options include_usage; Anthropic: read the final
  message_delta) to still bill/observe correctly.
- Behind a reverse proxy, disable response buffering or streaming silently
  degrades into a single blob at the end.
"""
import os


def openai_streaming(prompt: str) -> None:
    """Stream from OpenAI Chat Completions."""
    from openai import OpenAI

    client = OpenAI()  # reads OPENAI_API_KEY from the environment

    # stream=True flips the response into an iterator of incremental "delta"
    # chunks. include_usage asks the API to send a final chunk carrying the
    # token counts, which we otherwise lose in streaming mode.
    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are concise."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,          # low = focused, good for factual answers
        max_tokens=300,           # cap output: controls cost + latency
        stream=True,
        stream_options={"include_usage": True},
    )

    print("OpenAI: ", end="", flush=True)
    usage = None
    for chunk in stream:
        # The final usage-only chunk has an empty `choices` list, so guard it.
        if chunk.choices:
            delta = chunk.choices[0].delta.content
            if delta:
                print(delta, end="", flush=True)  # print as tokens arrive
        if chunk.usage:
            usage = chunk.usage
    print()
    if usage:
        # Real cost tracking lives here in production.
        print(f"  [tokens] in={usage.prompt_tokens} out={usage.completion_tokens}")


def anthropic_streaming(prompt: str) -> None:
    """Stream from Anthropic Claude Messages API."""
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY

    print("Claude: ", end="", flush=True)
    # The SDK's context-manager stream handles the SSE event types for you
    # (content_block_delta, message_delta, etc.) and exposes a simple
    # text_stream iterator of just the text pieces.
    with client.messages.stream(
        model="claude-sonnet-4-5",
        system="You are concise.",   # NOTE: system is a top-level field on Claude
        max_tokens=300,              # REQUIRED on Anthropic
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
        final = stream.get_final_message()  # carries usage after the stream ends
    print()
    print(f"  [tokens] in={final.usage.input_tokens} out={final.usage.output_tokens}")


if __name__ == "__main__":
    question = "In two sentences, why is streaming good UX for chatbots?"
    if os.getenv("OPENAI_API_KEY"):
        openai_streaming(question)
    if os.getenv("ANTHROPIC_API_KEY"):
        anthropic_streaming(question)
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        print("Set OPENAI_API_KEY and/or ANTHROPIC_API_KEY to run this example.")
