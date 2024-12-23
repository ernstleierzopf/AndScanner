import os
import shutil
from pathlib import Path
from romanalyzer_extractor.utils import execute
from romanalyzer_extractor.extractor.base import Extractor


class SonyImgExtractor(Extractor):
    def __init__(self, target, target_path=None):
        super().__init__(target, target_path)
        self.tool = Path('romanalyzer_extractor/tools/sony_dump_tool/sony_dump.x86_64').absolute()

    def extract(self):
        # if not self.chmod(): return None
        self.log.debug("Sin extract target: {}".format(self.target))
        self.log.debug("\tstart extract sin file.")

        abspath = self.target.absolute()
        extract_cmd = ' "{}" "{}" "{}"'.format(self.tool, "/tmp/out", abspath)
        output = execute(extract_cmd, suppress_output=True)
        data = output.split("\n")
        for line in data:
            if "Extracting " in line:
                self.extracted = self.target.parents[0] / line.replace("Extracting file /tmp/out/", "")
            if "Processing " in line:
                self.extracted = self.target.parents[0] / line.replace("Processing /tmp/out/", "")
            if " created." in line:
                self.extracted = self.target.parents[0] / line.replace(" created.", "").replace("/tmp/out/", "")

        for file in os.listdir("/tmp/out"):
            path = os.path.join("/tmp/out", file)
            if "." in file and file.rsplit(".", 1)[1].isnumeric():
                filename = file.rsplit(".", 1)[0] + ".img"
                newpath = os.path.join("/tmp/out", filename)
                shutil.move(path, newpath)
                path = newpath
                if file == self.extracted.name:
                    self.extracted = self.target.parents[0] / filename
            shutil.move(path, self.target.parents[0])

        if not self.extracted.exists():
            self.log.warn("\tfailed to extract {}".format(self.target))
            return None
        else:
            self.log.debug("\textracted path: {}".format(self.extracted))
            abspath.unlink()
            return self.extracted