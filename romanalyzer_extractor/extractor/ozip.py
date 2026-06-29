import shutil
import os
from pathlib import Path
from romanalyzer_extractor.utils import execute
from romanalyzer_extractor.extractor.base import Extractor
from romanalyzer_extractor.extractor.archive import ArchiveExtractor


class OZipExtractor(Extractor):
    def __init__(self, target, target_path=None):
        super().__init__(target, target_path)
        self.tool = Path('romanalyzer_extractor/tools/oppo_ozip_decrypt/ozipdecrypt.py').absolute()

    def extract(self):
        converted_zip = self.extracted.with_suffix("")
        tmp_dir = self.extracted.parent / "tmp"
        self.log.debug("OZip extract target: {}".format(converted_zip))
        self.log.debug("\tstart extract archive.")

        convert_cmd = 'python3 {decrypt_script} "{ozip}" "{tmp_path}"'.format(decrypt_script=self.tool, ozip=self.target.absolute(), tmp_path=tmp_dir)
        execute(convert_cmd)
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

        self.log.debug('\tconverted ozip to zip: {}'.format(converted_zip))

        extractor = ArchiveExtractor(converted_zip)
        extractor.target = converted_zip
        self.extracted = extractor.extract()
        if os.path.exists(converted_zip):
            os.path.unlink(converted_zip)
        if self.extracted and self.extracted.exists(): 
            self.log.debug("\textracted path: {}".format(self.extracted))
            return self.extracted
        else:
            self.log.warn("\tfailed to extract {} using unzip".format(converted_zip))
            return None
