import base64
import json
import re
import sys
import yaml
from pathlib import Path

from annotool.schema import PipelineConfig, TaskSchema

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def load_config(config_path: str) -> PipelineConfig:
    path = Path(config_path)
    if not path.exists():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(path) as f:
        raw = yaml.safe_load(f)

    required = {"input_dir", "output"}
    missing = required - raw.keys()
    if missing:
        print(f"Error: missing required config keys: {missing}", file=sys.stderr)
        sys.exit(1)

    # --- API keys ---
    api_keys: list[str] = []
    if "api_keys" in raw:
        api_keys = [str(k).strip() for k in raw["api_keys"] if str(k).strip()]

    # --- Task schema ---
    task_schema = TaskSchema()
    if "task_schema" in raw:
        schema_path = Path(raw["task_schema"])
        if not schema_path.exists():
            print(f"Error: task_schema file not found: {schema_path}", file=sys.stderr)
            sys.exit(1)
        task_schema = load_task_schema(str(schema_path))

    return PipelineConfig(
        input_dir=raw["input_dir"],
        output=raw["output"],
        model=raw.get("model", "gpt-4o-mini"),
        api_keys=api_keys,
        task_schema=task_schema,
        prompt_override=raw.get("prompt", ""),
    )


def load_task_schema(schema_path: str) -> TaskSchema:
    with open(schema_path) as f:
        raw = yaml.safe_load(f) or {}

    return TaskSchema(
        preset=raw.get("preset", "default"),
        labels=raw.get("labels") or [],
        output_fields=raw.get("output_fields") or [],
        include_caption=raw.get("include_caption", True),
    )


def collect_images(input_dir: str) -> list[Path]:
    directory = Path(input_dir)
    if not directory.exists():
        print(f"Error: input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)

    images = sorted(
        p for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    return images


def encode_image(image_path: Path) -> tuple[str, str]:
    suffix = image_path.suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(suffix, "image/jpeg")

    with open(image_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    return data, mime_type


def parse_json_response(text: str) -> tuple[dict, str | None]:
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text), None
    except json.JSONDecodeError:
        pass

    # Try extracting JSON block from markdown code fences
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1)), None
        except json.JSONDecodeError:
            pass

    # Try extracting the first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group()), None
        except json.JSONDecodeError:
            pass

    # Fallback: return raw text
    return {"raw": text}, "Could not parse JSON, storing raw response"


def save_results(results: list[dict], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
