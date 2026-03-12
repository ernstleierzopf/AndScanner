import os
from pathlib import Path
from romanalyzer_extractor.utils import execute
from romanalyzer_extractor.extractor.base import Extractor


class ErofsImgExtractor(Extractor):
    def __init__(self, target, target_path=None):
        super().__init__(target, target_path)
        self.tool = Path('romanalyzer_extractor/tools/huawei_erofs/erofsUnpackKt_x64').absolute()

    def extract(self):
        # if not self.chmod(): return None
        self.log.debug("Erofs extract target: {}".format(self.target))
        self.log.debug("\tstart extract erofs file.")

        abspath = self.target.absolute()
        # erofsUnpackKt_x64 can not handle paths correctly using "", so relative paths are used.
        cwd = os.getcwd()
        os.chdir(abspath.parent)
        self.log.debug(f"\t{abspath.parent}, cwd: {cwd}, {self.extracted}, {abspath.name}, {self.extracted.name}")

        extract_cmd = '{} "{}" "{}"'.format(self.tool, abspath.name, self.extracted.name)
        execute(extract_cmd, suppress_output=False)

        os.chdir(cwd)

        if not self.extracted.exists() or len(os.listdir(self.extracted)) == 0:
            self.log.warn("\tfailed to extract {}".format(self.target))
            return None
        else:
            self.log.debug("\textracted path: {}".format(self.extracted))
            return self.extracted
