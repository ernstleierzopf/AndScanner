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

        outpath = self.target.parents[0] / "out"
        if not os.path.exists(outpath):
            os.mkdir(outpath)
        abspath = self.target.absolute()
        extract_cmd = ' "{}" "{}" "{}"'.format(self.tool, outpath, abspath)
        output = execute(extract_cmd, suppress_output=True)
        data = output.split("\n")
        for line in data:
            if "Extracting file" in line:
                self.extracted = self.target.parents[0] / line.replace("Extracting file " + str(outpath) + "/", "")
            if "Processing " in line:
                self.extracted = self.target.parents[0] / line.replace("Processing " + str(outpath) + "/", "")
            if " created." in line:
                self.extracted = self.target.parents[0] / line.replace(" created.", "").replace(str(outpath) + "/", "")

        for file in os.listdir(outpath):
            path = os.path.join(outpath, file)
            if "." in file and file.rsplit(".", 1)[1].isnumeric():
                filename = file.rsplit(".", 1)[0] + ".img"
                newpath = os.path.join(outpath, filename)
                shutil.move(path, newpath)
                path = newpath
                if file == self.extracted.name:
                    self.extracted = self.target.parents[0] / filename
            shutil.move(path, self.target.parents[0])
        shutil.rmtree(outpath, ignore_errors=False)

        if not self.extracted.exists():
            self.log.warn("\tfailed to extract {}".format(self.target))
            return None
        else:
            self.log.debug("\textracted path: {}".format(self.extracted))
            abspath.unlink()
            return self.extracted