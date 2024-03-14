from pathlib import Path
from romanalyzer_extractor.utils import execute
from romanalyzer_extractor.extractor.base import Extractor
from romanalyzer_extractor.extractor.newdat import NewDatExtractor


class BrotliExtractor(Extractor):
    def __init__(self, target, target_path=None):
        super().__init__(target, target_path)
        self.tool = Path('romanalyzer_extractor/tools/brotli/brotli').absolute()

    def extract(self):
        self.log.debug("Brotli extract: {}".format(self.target))
        workdir = self.target.parents[0]

        output_new_dat = workdir / self.target.stem
        if not output_new_dat.exists():
            convert_cmd = '{brotli} --decompress "{new_dat_br}" -o "{new_dat}"'.format(
            #convert_cmd = 'cd {workdir} && {brotli} --decompress {new_dat_br} -o {new_dat}'.format(
                brotli=self.tool, new_dat_br=self.target, new_dat=output_new_dat
            )
            execute(convert_cmd)

        extractor = NewDatExtractor(output_new_dat)
        self.extracted = extractor.extract()
        if self.extracted and self.extracted.exists(): 
            self.log.debug("\textracted path: {}".format(self.extracted))
            self.target.unlink()
            return self.extracted
        else:
            self.log.warn("\tfailed to extract {}".format(self.target))
            return None
