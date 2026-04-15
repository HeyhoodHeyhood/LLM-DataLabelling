from annotool.api import ClientPool, annotate_image
from annotool.schema import PipelineConfig
from annotool.utils import collect_images, save_results


def run(config: PipelineConfig) -> None:
    images = collect_images(config.input_dir)

    if not images:
        print(f"No supported images found in: {config.input_dir}")
        return

    pool = ClientPool(config.api_keys)
    key_info = f"{pool.size} key(s)" if pool.size > 1 else "1 key"
    print(f"Found {len(images)} image(s). Model: {config.model}. API keys: {key_info}.\n")

    results = []

    for image_path in images:
        print(f"Processing {image_path.name}...")

        try:
            annotation = annotate_image(image_path, config.model, config.prompt, pool)
            entry = {
                "image": image_path.name,
                "annotation": annotation,
            }
        except Exception as exc:
            print(f"  Error [{image_path.name}]: {exc}")
            entry = {
                "image": image_path.name,
                "annotation": None,
                "error": str(exc),
            }

        results.append(entry)

    save_results(results, config.output)
    print(f"\nDone. {len(results)} annotation(s) saved to: {config.output}")
