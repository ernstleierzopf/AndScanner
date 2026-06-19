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

        if self.target.name == "userdata.sin":
            self.log.debug("\tSkipping userdata.sin extraction.")
            return None

        outpath = "/tmp/out"
        if not os.path.exists(outpath):
            os.mkdir(outpath)
        abspath = self.target.absolute()
        tmppath = os.path.join("/tmp", self.target.name)
        extract_cmd = ' "{}" "{}" "{}"'.format(self.tool, outpath, tmppath)
        shutil.move(abspath, tmppath)
        output = execute(extract_cmd, suppress_output=True)
        shutil.move(tmppath, abspath)
        data = output.split("\n")
        for line in data:
            if "Extracting file" in line:
                self.extracted = self.target.parents[0] / line.replace("Extracting file " + str(outpath) + "/", "")
            if "Processing " in line:
                self.extracted = self.target.parents[0] / line.replace("Proccessing " + str(outpath) + "/", "").replace("...", "")
            if " created." in line:
                self.extracted = self.target.parents[0] / line.replace(" created.", "").replace(str(outpath) + "/", "")
            if " succeed." in line:
                self.extracted = self.target.parents[0] / line.replace(" succeed.", "").replace("Renaming to ", "").replace(str(outpath) + "/", "")
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
            self.log.warn("\tfailed to extract {}, {}".format(self.target, self.extracted))
            return None
        else:
            self.log.debug("\textracted path: {}".format(self.extracted))
            abspath.unlink()
            return self.extracted
