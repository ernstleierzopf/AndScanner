import subprocess
import shutil
import os
from romanalyzer_extractor.extractor.base import Extractor


class YaffsImgExtractor(Extractor):
    def extract(self):
        if not self.chmod(): return None
        abspath = self.target.absolute()
        cmd = f'unyaffs "{abspath}" "{self.extracted}"'
        if os.getuid() != 0:  # non-root user
            self.log.debug("\tpython script not running as root. Adding sudo to mount command.")
            cmd = "sudo " + cmd
        if self.target.endswith(".unknown") and self.extracted.endswith(".unknown.extracted"):
            self.extracted = self.extracted.replace(".unknown.extracted", "")
        try:
            if not os.path.exists(self.extracted):
                os.mkdir(self.extracted)
            subprocess.check_call(cmd, shell=True, encoding='utf-8')
        except subprocess.CalledProcessError as e:
            self.log.error(f"Could not extract {self.target} to {self.extracted}. Skipping {self.target}..")
            self.log.error(e)

        if self.extracted is None or not self.extracted.exists():
            self.log.warn("\tfailed to extract {}".format(self.target))
            return None
        else:
            self.log.debug("\textracted path: {}".format(self.extracted))
            abspath.unlink()
            return self.extracted
