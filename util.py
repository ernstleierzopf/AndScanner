import json
import os
import shutil
import sys
import time
from pathlib import Path

from romanalyzer_extractor.extractor.rom import ROMExtractor
from romanalyzer_patch.analysis.TestEngine import TestEngine


# Path to the config file.
CONFIG_FILE = "./config.json"


def validate(api_level: int):
    """
    Function to validate if the Android image API level is supported by the scanner.
    api_level: Android API level of the image.
    """
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    # Validate API level support.
    if api_level < config["MIN_SUPPORTED_API_LEVEL"]:
        print(f"Android API level {api_level} is too low. \n"
              f"Minimum supported API Level is {config['MIN_SUPPORTED_API_LEVEL']}\n")

        # Terminate program execution.
        sys.exit(1)

    if api_level > config["MAX_SUPPORTED_API_LEVEL"]:
        print(f"Android API level {api_level} is too high. \n"
              f"Maximum supported API Level is {config['MAX_SUPPORTED_API_LEVEL']}\n")

        # Terminate program execution.
        sys.exit(1)


def transform_path(extracted_image_path: str):
    # Search for build.prop file in system dir.
    path_input = ''
    extracted_image_path = Path(extracted_image_path)
    for path in extracted_image_path.rglob("**/*system*/build.prop"):
        path_input = path
        break

    # Check for false-y value.
    if not path_input:
        raise Exception("Missing build.prop file")

    path_input = os.path.abspath(path_input)

    index0 = path_input.find('\n')
    path_input = path_input[:index0]

    index1 = path_input.rfind('/')
    str1 = path_input[:index1]

    index2 = str1.rfind('/')
    str2 = str1[:index2]

    dir1 = path_input[index2:index1][1:]

    if dir1 != 'system':
        os.rename(str1, str2 + '/system')

    return str2 + '/'


def get_extracted_image_dir_path(image_path_input: str, extraction_path: str):
    image_path = Path(image_path_input).absolute()
    if extraction_path is not None:
        image_path = Path(f"{extraction_path}/{image_path.name}")
    return str(ROMExtractor(image_path).extracted) + "/"


def extract_zip(image_path_input: str, extraction_path: str):
    # Create Path object.
    image_path = Path(image_path_input).absolute()

    # Extract image.
    extracted_image_dir_path = ROMExtractor(image_path, extraction_path).extract()

    print(f"{extracted_image_dir_path}/")
    return str(extracted_image_dir_path) + '/'


def extract_image(image_path: str, extraction_path: str):
    """
    :path: path to the image
    :api_level: Android API level of the image
    """
    # Check if path points to a directory.
    _image_path = Path(image_path).absolute()
    if _image_path.is_dir():
        return image_path

    extracted_image_path = get_extracted_image_dir_path(image_path, extraction_path)
    if os.path.exists(extracted_image_path):
        print("Extracted image path already exists at %s. Skipping.." % extracted_image_path)
        return extracted_image_path
    if os.path.exists(os.path.join(extraction_path, "file_metadata.csv")):
        os.remove(os.path.join(extraction_path, "file_metadata.csv"))
    if os.path.exists(os.path.join(extraction_path, "vbmeta_digests.csv")):
        os.remove(os.path.join(extraction_path, "vbmeta_digests.csv"))

    # Extract the image zip, if required.
    extracted_image_path = extract_zip(image_path, extraction_path)

    return extracted_image_path


def run_vulnerability_scan(image_path: str, extracted_image_path: str, report_base_path: str):
    report_dir = Path(report_base_path).absolute() / "reports" / "patch_analyzer_reports"
    report_file = report_dir / (os.path.basename(image_path) + ".txt")

    if not report_dir.exists():
        os.makedirs(report_dir)

    firmware = transform_path(extracted_image_path)
    print(firmware)

    # Run the patch analysis.
    test_engine = TestEngine(firmware)
    reports = test_engine.runAllVulnLogicTest()
    print(reports)

    # Saving the reports.
    with open(report_file, "w") as f:
        json.dump(reports, f, indent=2)


def run_app_analyzer(image_path: str, extracted_image_path: str, report_base_path: str):
    # Build reports dir path.
    report_dir = Path(report_base_path).absolute() / "reports" / "app_analyzer_apk_reports"

    if not report_dir.exists():
        os.makedirs(report_dir)

    for root, dirs, files in os.walk(extracted_image_path):
        for file_str in files:
            if file_str.endswith('.apk'):
                path_str = os.path.join(root, file_str)

                # Build report target destination.
                report_path = report_dir / os.path.basename(image_path) / file_str

                # Build APK file analysis command.
                command_str = f"python3 ./app_analyzer/analyze_apps.py -i {path_str} -r {report_path}"

                # Execute APK file analysis command.
                return_code = os.system(command_str)

                if return_code == 2:
                    sys.exit(2)
