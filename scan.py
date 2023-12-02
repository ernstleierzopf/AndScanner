import os
import sys
import json
from scan_util import extract_image, run_vulnerability_scan, run_app_analyzer


def scan(image_path: str, vendor: str, api_level: int):
    # Extract image.
    extracted_image_path = extract_image(image_path, vendor, api_level)

    # Run vulnerability scan.
    run_vulnerability_scan(extracted_image_path)

    # Run app analyzer.
    run_app_analyzer(extracted_image_path)


def single_scan(image_path: str):
    try:
        vendor = sys.argv[2]
    except Exception:
        raise Exception("Missing vendor name")

    try:
        api_level = int(sys.argv[3])
    except ValueError:
        raise Exception("Invalid Android API level")
    except Exception:
        raise Exception("Missing image Android API level")

    # Start scan.
    scan(image_path, vendor, api_level)


def batch_scan(scan_queue: []):
    # Scan each image.
    for index, image in enumerate(scan_queue):
        try:
            image_path = image["path"]
        except Exception:
            raise Exception(f"Missing image path for image {index}")

        try:
            vendor = image["vendor"]
        except Exception:
            raise Exception(f"Missing vendor name for image {index}")

        try:
            api_level = image["api_level"]
        except Exception:
            raise Exception(f"Missing Android API level for image {index}")

        # Start scan.
        scan(image_path, vendor, api_level)


if __name__ == "__main__":
    assert sys.argv[1], "Missing image path or path to json file"

    file_path = os.path.abspath(sys.argv[1])  # could be image path or batch scan json file path.
    filename, file_extension = os.path.splitext(file_path)

    # Batch Scan.
    if file_extension.lower() == ".json":
        # Parse the JSON file.
        with open(file_path, "r") as f:
            parsed_scan_queue = json.load(f)

        # Scan the images.
        batch_scan(parsed_scan_queue)

    # Single Scan.
    else:
        single_scan(file_path)
