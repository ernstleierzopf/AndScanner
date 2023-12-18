from pathlib import Path

from romanalyzer_extractor.utils import execute
from romanalyzer_extractor.extractor.base import Extractor


class ExtImgExtractor(Extractor):
    def __init__(self, target):
        super().__init__(target)
        self.tool = Path('romanalyzer_extractor/tools/extfstools/ext2rd').absolute()

    def extract(self):
        if not self.chmod(): 
            return
        
        self.extracted = self.target.parents[0] / (self.target.name + '.extracted')
        
        if not self.extracted.exists(): 
            self.extracted.mkdir()

        # Parts of extraction command.
        extfstool = self.tool
        extimg = self.target
        outdir = self.extracted

        # Build extraction command.
        extract_cmd = f"{extfstool} {extimg} ./:{outdir}"

        # Perform extraction.
        execute(extract_cmd)

        if self.extracted and self.extracted.exists(): 
            self.log.debug(f"\textracted path: {self.extracted}")
            return self.extracted
        else:
            self.log.warning(f"\tfailed to extract {self.target}")
            return None
