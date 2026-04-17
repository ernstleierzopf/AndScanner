import traceback
from pathlib import Path
from romanalyzer_extractor.utils import execute
from romanalyzer_extractor.extractor.base import Extractor


class BootImgExtractor(Extractor):
    def __init__(self, target, target_path=None):
        super().__init__(target, target_path)
        self.tool = Path("romanalyzer_extractor/tools/bootimg_extraction/unpack_bootimg.py").absolute()
        self.tool2 = Path("romanalyzer_extractor/tools/bootimg_extraction/unpack_bootimg_old.py").absolute()

    def extract(self):
        if not self.chmod():
            return

        self.log.debug(f"Bootimg extract: {self.target}")
        self.log.debug("\tstart extract target")

        # Parts of extraction command.
        workdir = self.target.parent
        boot_img = self.target.absolute()
        self.extracted = workdir / self.target.stem

        # Build extraction command.
        extract_cmd = f"cd \"{workdir}\" && {self.tool} --boot_img \"{boot_img}\" --out \"{self.extracted}\""
        extract_cmd2 = f"cd \"{workdir}\" && {self.tool2} --boot_img \"{boot_img}\" --out \"{self.extracted}\""

        # Perform extraction.
        output, exit_code = execute(extract_cmd, return_exit_code=True, redirect_stderr_stdout=True)
        if exit_code != 0:
            output2, exit_code = execute(extract_cmd2, return_exit_code=True, redirect_stderr_stdout=True)
            if exit_code != 0:
                self.log.error(f"failed to extract {boot_img}.")
                self.log.error(output)
                self.log.error(output2)

        if not self.extracted.exists():
            self.log.warn("\tfailed to extract {}".format(self.target))
            return None
        else:
            self.log.debug("\textracted path: {}".format(self.extracted))
            return self.extracted
