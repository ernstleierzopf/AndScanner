import os
from pathlib import Path
from romanalyzer_extractor.utils import execute
from romanalyzer_extractor.extractor.base import Extractor


class OfpExtractor(Extractor):
    def __init__(self, target, target_path=None):
        super().__init__(target, target_path)
        self.tool = Path('romanalyzer_extractor/tools/ofp/ofp_qc_decrypt.py').absolute()
        self.tool_mtk = Path('romanalyzer_extractor/tools/ofp/ofp_mtk_decrypt.py').absolute()

    def extract(self):
        # if not self.chmod(): return None
        self.log.debug("Ofp extract target: {}".format(self.target))
        self.log.debug("\tstart extract ofp file.")

        abspath = self.target.absolute()
        
        extract_cmd = 'python3 {} "{}" "{}"'.format(self.tool, abspath, self.extracted)
        try:
            execute(extract_cmd)
        except Exception:
            pass

        if len(os.listdir(self.extracted)) == 0:
            extract_cmd = 'python3 {} "{}" "{}"'.format(self.tool_mtk, abspath, self.extracted)
            execute(extract_cmd)

        if not self.extracted.exists() or len(os.listdir(self.extracted)) == 0:
            self.log.warn("\tfailed to extract {}".format(self.target))
            return None
        else:
            self.log.debug("\textracted path: {}".format(self.extracted))
            abspath.unlink()
            return self.extracted
