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
    # Get the path to the build.prop file.
    # if os.path.exists(f"{extracted_image_path}/system/system/build.prop"):
    #     path_input = f"{extracted_image_path}/system/system/build.prop"
    # else:
    #     path_input = os.popen(f'find {extracted_image_path} -name "build.prop" -size +1k').read()

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


def get_extracted_image_dir_path(image_path_input: str, vendor: str, extraction_path: str):
    # image_path = Path(image_path_input).absolute()
    # parent_dir_path = image_path.parent
    # if vendor == "zte":
    #     extracted_dir_name = f"ZTE_Rom_{str(time.time())}.extracted"
    #     extracted_image_dir_path = parent_dir_path / extracted_dir_name
    #     return ROMExtractor(extracted_image_dir_path).extracated
    # elif vendor == "huawei":
    #     return ROMExtractor(os.path.abspath(image_path)).extracted
    image_path = Path(image_path_input).absolute()
    if extraction_path is not None:
        image_path = Path(f"{extraction_path}/{image_path.name}")
    return str(ROMExtractor(image_path).extracted) + "/"


def extract_zip(image_path_input: str, vendor: str, extraction_path: str):
    # Create a Path object for the image path and convert it to the absolute path.
    image_path = Path(image_path_input).absolute()

    # Path to the parent directory.
    parent_dir_path = image_path.parent

    # Vendor ZTE has a different compression format, requires special extraction approach.
    if vendor == "zte":
        # Directory name of the extracted image zip.
        extracted_dir_name = f"ZTE_Rom_{str(time.time())}.extracted"

        # Build the extracted image directory absolute path.
        extracted_image_dir_path = parent_dir_path / extracted_dir_name

        # Build the unzip command.
        unzip_command = f"unzip -o {image_path} -d {extracted_image_dir_path}"
        # Unzip image zip.
        os.system(unzip_command)

        for root, dirs, files in os.walk(extracted_image_dir_path):
            for d in dirs:
                os.rename(os.path.join(root, d), os.path.join(root, 'ZTE_Rom_' + str(time.time())))

        extracted_image_dir_path = ROMExtractor(extracted_image_dir_path).extract()

        # Extract system.img, if not extracted already.
        if not Path(f"{extracted_image_dir_path}/system.img.extracted").exists():
            # Create the absolute path to the system.img file.
            system_img_path = Path(extracted_image_dir_path).absolute() / "system.img"

            # Get working path.
            work_path = Path(__file__).absolute().parent

            # ***
            # *** Special Step 1: Extract the super.img.ext4 file ***
            # ***
            # Build path to "ext2rd" tool binary.
            ext2rd_tool = work_path / "romanalyzer_extractor/tools/extfstools/ext2rd"

            # Build paths to source and target dirs.
            source_dir = str(system_img_path)[:-1] + ' ./:'
            target_dir = str(system_img_path)[:-1] + '.extracted'

            # Unpack the system.img file using ext2rd.
            os.system(f"{ext2rd_tool} {source_dir} {target_dir}")
            # *** end of special step 1 ***

        print(extracted_image_dir_path)
        return extracted_image_dir_path

    # Vendor Huawei has a different compression format, requires special extraction approach.
    elif vendor == "huawei":
        extracted_image_dir_path = ROMExtractor(os.path.abspath(image_path)).extract()

        # Make a temporary directory in the extracted image directory.
        os.system(f"mkdir {extracted_image_dir_path}/tmp")

        # Get the working path.
        work_path = Path(__file__).absolute().parent

        # ***
        # *** Special Step 1: Extract the super.img.ext4 file ***
        # ***
        # Build path to "lp unpack" tool binary.
        lpunpack_tool = work_path / "romanalyzer_extractor/tools/huawei_erofs/lpunpack"

        # Build paths to source and target dirs.
        source_dir = extracted_image_dir_path / "UPDATE.APP.extracted/SUPER.img.ext4"
        target_dir = extracted_image_dir_path / "tmp"

        # Unpack the super.img.ext4 file using lpunpack.
        os.system(f"{lpunpack_tool} {source_dir} {target_dir}")
        # *** end of special step 1 ***

        # ***
        # *** Special Step 2: Extracting the system.img file ***
        # ***
        # Build path to "erofsUnpack" tool binary.
        erofsunpack_tool = work_path / "romanalyzer_extractor/tools/huawei_erofs/erofsUnpackKt_x64"

        # Build paths to source and target dirs.
        source_dir = extracted_image_dir_path / "/tmp/system.img"
        target_dir = extracted_image_dir_path / "sys"

        # Extract the system.img file using erofsUnpack.
        os.system(f"{erofsunpack_tool} {source_dir} {target_dir}")
        # ** end of special step 2 ***

        # Update the extracted image path.
        extracted_image_dir_path = extracted_image_dir_path / "sys"

        print(f"Extracted image to: {extracted_image_dir_path}")
        return extracted_image_dir_path

    # Default extraction process.
    else:
        # Create Path object.
        image_path = Path(image_path_input).absolute()

        # Extract image.
        extracted_image_dir_path = ROMExtractor(image_path, extraction_path).extract()

        print(f"{extracted_image_dir_path}/")
        return str(extracted_image_dir_path) + '/'


def extract_image(image_path: str, vendor: str, extraction_path: str):
    """
    :path: path to the image
    :vendor: name of the image vendor
    :api_level: Android API level of the image
    """
    # Check if path points to a directory.
    _image_path = Path(image_path).absolute()
    if _image_path.is_dir():
        # raise Exception("image path points to a directory, not a zip file.")
        return image_path

    extracted_image_path = get_extracted_image_dir_path(image_path, vendor, extraction_path)
    if os.path.exists(extracted_image_path):
        print("Extracted image path already exists at %s. Skipping.." % extracted_image_path)
        return extracted_image_path

    # Remove any previously existing extracted directory.
    # _image_path = Path(f"{image_path}.extracted").absolute()
    # if _image_path.exists():
    #     shutil.rmtree(_image_path)

    # Extract the image zip, if required.
    extracted_image_path = extract_zip(image_path, vendor, extraction_path)

    return extracted_image_path


def run_vulnerability_scan(image_path: str, extracted_image_path: str):
    report_dir = Path(image_path).absolute().parent / "reports" / "patch_analyzer_reports"
    report_file = report_dir / "patch_analysis_reports.txt"

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
        f.write(str(reports))


def run_app_analyzer(image_path: str, extracted_image_path: str):
    # Build reports dir path.
    report_dir = Path(image_path).absolute().parent / "reports" / "app_analyzer_apk_reports"

    if not report_dir.exists():
        os.makedirs(report_dir)

    for root, dirs, files in os.walk(extracted_image_path):
        for file_str in files:
            if file_str.endswith('.apk'):
                path_str = os.path.join(root, file_str)

                # Build report target destination.
                report_path = report_dir / path_str.replace('/', '_')

                # Build APK file analysis command.
                command_str = f"python3 ./app_analyzer/analyze_apps.py -i {path_str} -r {report_path}"

                # Execute APK file analysis command.
                return_code = os.system(command_str)

                if return_code == 2:
                    sys.exit(2)
