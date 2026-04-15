import itertools
import os
from pathlib import Path

from openai import OpenAI

from annotool.utils import encode_image, parse_json_response

# ---------------------------------------------------------------------------
# Multi-key client pool (round-robin)
# ---------------------------------------------------------------------------

def _build_clients(api_keys: list[str]) -> list[OpenAI]:
    """
    Build one OpenAI client per key.
    Falls back to OPENAI_API_KEY env var (supports comma-separated keys).
    """
    keys = api_keys[:]

    if not keys:
        env = os.environ.get("OPENAI_API_KEY", "")
        keys = [k.strip() for k in env.split(",") if k.strip()]

    if not keys:
        # Let OpenAI SDK raise its own error
        return [OpenAI()]

    return [OpenAI(api_key=k) for k in keys]


class ClientPool:
    """Round-robin pool of OpenAI clients."""

    def __init__(self, api_keys: list[str]) -> None:
        clients = _build_clients(api_keys)
        self._cycle = itertools.cycle(clients)
        self.size = len(clients)

    def next(self) -> OpenAI:
        return next(self._cycle)


# ---------------------------------------------------------------------------
# Annotation call
# ---------------------------------------------------------------------------

def annotate_image(
    image_path: Path,
    model: str,
    prompt: str,
    pool: ClientPool,
) -> dict:
    """
    Send image to OpenAI Vision API and return parsed annotation dict.
    On JSON parse failure, returns {"raw": <response_text>} with a warning printed.
    """
    b64_data, mime_type = encode_image(image_path)
    client = pool.next()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{b64_data}",
                            "detail": "auto",
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
        max_tokens=1024,
    )

    raw_text = response.choices[0].message.content or ""
    annotation, warning = parse_json_response(raw_text)

    if warning:
        print(f"  Warning [{image_path.name}]: {warning}")

    return annotation
