from pathlib import Path
from romanalyzer_extractor.utils import execute
from romanalyzer_extractor.extractor.base import Extractor


class BootImgExtractor(Extractor):
    def __init__(self, target, target_path=None):
        super().__init__(target, target_path)
        self.tool = Path("romanalyzer_extractor/tools/bootimg_extraction/unpack_bootimg.py").absolute()

    def extract(self):
        if not self.chmod():
            return

        self.log.debug(f"Bootimg extract: {self.target}")
        self.log.debug("\tstart extract target")

        # Parts of extraction command.
        workdir = self.target.parent
        split_boot = self.tool
        boot_img = self.target.absolute()
        self.extracted = workdir / self.target.stem

        # Build extraction command.
        extract_cmd = f"cd {workdir} && {split_boot} --boot_img \"{boot_img}\" --out \"{self.extracted}\""

        # Perform extraction.
        execute(extract_cmd)

        if not self.extracted.exists():
            self.log.warn("\tfailed to extract {}".format(self.target))
            return workdir
        else:
            self.log.debug("\textracted path: {}".format(self.extracted))
            return self.extracted
