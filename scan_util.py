import os
import sys
import time

from romanalyzer_extractor.extractor.rom import ROMExtractor
from romanalyzer_extractor.extractor.ota import AndrOtaPayloadExtractor
from romanalyzer_patch.analysis.TestEngine import TestEngine


def transform_path(extracted_image_path: str):
    # Get the path to the build.prop file.
    path_input = os.popen(f'find {extracted_image_path} -name "build.prop" -size +1k').read()

    if path_input == '':
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


def extract_image(image_path: str, vendor: str, api_level: int):
    """
    :path: path to the image
    :vendor: name of the image vendor
    :api_level: Android API level of the image
    """

    # A/B System Updates was introduced in API level 24. API level 24+ require a different extraction approach.
    extractor = ROMExtractor if api_level < 24 else AndrOtaPayloadExtractor

    # Vendor ZTE has a different image structure, requires special extraction approach.
    if vendor == "zte":
        path_zip = os.path.abspath(image_path)
        path1 = path_zip[:path_zip.rfind('/') + 1]
        path_extract = path1 + 'ZTE_Rom_' + str(time.time()) + '.extracted'
        os.system('unzip -o ' + path_zip + ' -d ' + path_extract)

        for root, dirs, files in os.walk(path_extract):
            for d in dirs:
                os.rename(os.path.join(root, d), os.path.join(root, 'ZTE_Rom_' + str(time.time())))

        extracted = extractor(path_extract).extract()

        if os.popen(f'find {path_extract} -name "system.img.extracted"').read() == '':
            path_img = os.popen(f'find {path_extract} -name "system.img"').read()

            path2 = str(os.path.abspath(sys.argv[0]))
            work_path = path1[:path2.rfind('/')]
            os.system(work_path + '/romanalyzer_extractor/tools/extfstools/ext2rd '
                      + str(path_img)[:-1] + ' ./:'
                      + str(path_img)[:-1] + '.extracted')

        print(path_extract)

        return path_extract

    # Vendor Huawei has a different image structure, requires special extraction approach.
    elif vendor == "huawei":
        extracted = extractor(os.path.abspath(image_path)).extract()

        os.system('mkdir ' + str(extracted) + '/tmp')

        path1 = str(os.path.abspath(sys.argv[0]))
        work_path = path1[:path1.rfind('/')]

        os.system(work_path + '/romanalyzer_extractor/tools/huawei_erofs/lpunpack ' + str(extracted)
                  + '/UPDATE.APP.extracted/SUPER.img.ext4 ' + str(extracted) + '/tmp')

        os.system(work_path + '/romanalyzer_extractor/tools/huawei_erofs/erofsUnpackKt_x64 ' + str(extracted)
                  + '/tmp/system.img ' + str(extracted) + '/sys')

        print(str(extracted) + '/sys/')

        return str(extracted) + '/sys/'

    else:
        extracted = extractor(os.path.abspath(image_path)).extract()

        print(str(extracted) + '/')

        return str(extracted) + '/'


def run_vulnerability_scan(extracted_image_path: str):
    firmware = transform_path(extracted_image_path)

    print(firmware)

    test_engine = TestEngine(firmware)
    reports = test_engine.runAllVulnLogicTest()

    print(reports)


def run_app_analyzer(extracted_image_path: str):
    parent_dir = os.path.dirname(extracted_image_path)
    report_dir = os.path.join(parent_dir, '.apk_report/')

    for root, dirs, files in os.walk(extracted_image_path):
        for file_str in files:
            if file_str.endswith('.apk'):
                path_str = os.path.join(root, file_str)
                report_path = report_dir + '/' + path_str.replace('/', '_')
                command_str = 'python ./static/androguard-3.3.6/main.py -i ' + path_str + ' -r ' + report_path
                os.system(command_str)