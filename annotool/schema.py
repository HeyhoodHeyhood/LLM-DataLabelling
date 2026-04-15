from dataclasses import dataclass, field
from typing import Any


@dataclass
class ObjectAnnotation:
    label: str
    description: str


@dataclass
class ImageAnnotation:
    objects: list[ObjectAnnotation]
    caption: str


@dataclass
class AnnotationResult:
    image: str
    annotation: dict[str, Any]  # parsed JSON or raw fallback
    error: str | None = None


# ---------------------------------------------------------------------------
# TaskSchema: defines the annotation output format requested by the user
# ---------------------------------------------------------------------------

PRESET_PROMPTS: dict[str, str] = {
    "default": (
        "Analyze this image and return STRICT JSON ONLY with no extra text:\n"
        '{\n'
        '  "objects": [\n'
        '    {\n'
        '      "label": "<object name>",\n'
        '      "description": "<brief description>"\n'
        '    }\n'
        '  ],\n'
        '  "caption": "<one sentence describing the full image>"\n'
        '}'
    ),
    "coco": (
        "Analyze this image. Return STRICT JSON ONLY. "
        "For each detected object estimate a normalized bounding box "
        "[x_center, y_center, width, height] where all values are 0.0-1.0.\n"
        '{\n'
        '  "categories": ["<label1>", "<label2>"],\n'
        '  "objects": [\n'
        '    {\n'
        '      "label": "<object name>",\n'
        '      "bbox": [x_center, y_center, width, height]\n'
        '    }\n'
        '  ],\n'
        '  "caption": "<one sentence describing the full image>"\n'
        '}'
    ),
    "yolo": (
        "Analyze this image. Return STRICT JSON ONLY. "
        "Assign a 0-based class_id to each unique label in the order they first appear. "
        "Estimate a normalized bounding box [x_center, y_center, width, height] "
        "where all values are 0.0-1.0.\n"
        '{\n'
        '  "labels": ["<label0>", "<label1>"],\n'
        '  "objects": [\n'
        '    {\n'
        '      "class_id": 0,\n'
        '      "bbox": [x_center, y_center, width, height]\n'
        '    }\n'
        '  ]\n'
        '}'
    ),
}


@dataclass
class TaskSchema:
    preset: str = "default"          # default / coco / yolo / custom
    labels: list[str] = field(default_factory=list)
    output_fields: list[str] = field(default_factory=list)
    include_caption: bool = True

    def build_prompt(self) -> str:
        if self.preset in PRESET_PROMPTS:
            return PRESET_PROMPTS[self.preset]

        # custom preset: build prompt from fields
        fields_desc = ", ".join(self.output_fields) if self.output_fields else "label, description"
        label_hint = ""
        if self.labels:
            label_hint = f" Only detect these categories: {', '.join(self.labels)}."

        caption_field = ',\n  "caption": "<one sentence>"' if self.include_caption else ""
        field_example = "\n".join(f'      "{f}": "<value>",' for f in (self.output_fields or ["label", "description"]))

        return (
            f"Analyze this image and return STRICT JSON ONLY.{label_hint}\n"
            f"Each detected object must have these fields: {fields_desc}.\n"
            '{\n'
            '  "objects": [\n'
            '    {\n'
            f'{field_example}\n'
            '    }\n'
            '  ]'
            f'{caption_field}\n'
            '}'
        )


# ---------------------------------------------------------------------------
# PipelineConfig
# ---------------------------------------------------------------------------

@dataclass
class PipelineConfig:
    input_dir: str
    output: str
    model: str = "gpt-4o-mini"
    api_keys: list[str] = field(default_factory=list)  # rotated round-robin
    task_schema: TaskSchema = field(default_factory=TaskSchema)

    # Allow explicit prompt override (takes priority over task_schema)
    prompt_override: str = ""

    @property
    def prompt(self) -> str:
        if self.prompt_override:
            return self.prompt_override
        return self.task_schema.build_prompt()
