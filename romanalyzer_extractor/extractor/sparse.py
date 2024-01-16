from pathlib import Path
from romanalyzer_extractor.utils import execute
from romanalyzer_extractor.extractor.base import Extractor
from romanalyzer_extractor.extractor.archive import ArchiveExtractor


class SparseImgExtractor(Extractor):
    def __init__(self, target):
        super().__init__(target)
        self.tool = Path('romanalyzer_extractor/tools/android-simg2img/simg2img').absolute()

    def extract(self):
        if not self.chmod(): return None

        self.log.debug("sparse image: {}".format(self.target))
        self.log.debug("\tstart convert sparse img to raw img")
        
        if str(self.target).endswith("sparsechunk.0"):
            convert_cmd = '{simg2img} {sparse_img} {output}'.format(
                    simg2img=self.tool, 
                    sparse_img=Path(str(self.target).replace("sparsechunk.0", "sparsechunk.*")), 
                    output=Path(str(self.target).replace("_sparsechunk.0", ".raw")))
            execute(convert_cmd)
            raw_img = Path(str(self.target).replace("_sparsechunk.0", ".raw"))
        elif "sparsechunk" in str(self.target):
            return None
        else:
            raw_img = self.target.parents[0] / (self.target.name+'.raw')
            convert_cmd = '{simg2img} "{sparse_img}" "{output}"'.format(
                    simg2img=self.tool, 
                    sparse_img=self.target.absolute(), 
                    output=raw_img)
            execute(convert_cmd)

            self.log.debug("\tconverted raw image: {}".format(raw_img))

        extractor = ArchiveExtractor(raw_img)
        self.extracted = extractor.extract()

        if self.extracted is None or not self.extracted.exists(): 
            self.log.warn("\tfailed to extract {}".format(self.target))
            return None
        else:
            self.log.debug("\textracted path: {}".format(self.extracted))
            return self.extracted
