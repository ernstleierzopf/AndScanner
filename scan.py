import os
import sys
import json
from util import validate, extract_image, run_vulnerability_scan, run_app_analyzer
from pathlib import Path


def single_scan(image_path: str):
    extraction_path = str(Path(sys.argv[2]).absolute())
    if extraction_path is not None and not os.path.exists(extraction_path):
        raise Exception(f"{extraction_path} does not exist!")

    #try:
    #    api_level = abs(int(sys.argv[3]))
    #except ValueError:
    #    raise Exception("Invalid Android API level")
    #except Exception:
    #    raise Exception("Missing image Android API level")

    # Begin scan.
    print("Scanning image")
    print(f"Image path: {image_path}",
    #      f"API Level : {api_level}",
          sep="\n")

    if len(sys.argv) == 4 and sys.argv[3] == "":
        del sys.argv[3]
    if len(sys.argv) < 4 or (len(sys.argv) == 4 and sys.argv[3] == "--extract"):
        # Extracting image.
        print("Extracting image")
        extracted_image_path = extract_image(image_path, extraction_path)

    if len(sys.argv) < 4 or (len(sys.argv) == 4 and sys.argv[3] == "--scan"):
        # Run vulnerability scan.
        print("Running vulnerability scans")
        run_vulnerability_scan(image_path, extracted_image_path, extraction_path)

        # Run app analyzer.
        print("Running app analyzer")
        run_app_analyzer(image_path, extracted_image_path, extraction_path)


# def batch_scan(scan_queue: []):
#     # Scan each image.
#     for index, image in enumerate(scan_queue):
#         try:
#             image_path = image["path"]
#         except Exception:
#             raise Exception(f"Missing image path for image {index}")
#
#         try:
#             api_level = image["api_level"]
#         except Exception:
#             raise Exception(f"Missing Android API level for image {index}")
#
#         # Start scan.
#         print(f"Scanning image {index + 1}")
#         scan(image_path, api_level)


if __name__ == "__main__":
    assert sys.argv[1], "Missing image path or path to json file"

    file_path = os.path.abspath(sys.argv[1])  # could be image path or batch scan json file path.
    filename, file_extension = os.path.splitext(file_path)
    single_scan(file_path)

    # # Batch Scan.
    # if file_extension.lower() == ".json":
    #     # Parse the JSON file.
    #     with open(file_path, "r") as f:
    #         parsed_scan_queue = json.load(f)
    #
    #     batch_scan(parsed_scan_queue)
    #
    # # Single Scan.
    # else:
    #     single_scan(file_path)
