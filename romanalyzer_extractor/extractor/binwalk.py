from romanalyzer_extractor.utils import execute
from romanalyzer_extractor.extractor.base import Extractor


class BinwalkExtractor(Extractor):

    def extract(self):
        """Using binwalk to extract files recursively and return extracted path."""

        self.log.debug("binwalk target: {}".format(self.target))
        self.log.debug("\tstart extract target")
        dirname = self.target.parents[0]
        cmd = 'binwalk --directory={} -Me "{}" '.format(dirname, self.target)
        execute(cmd)

        extracted = '_' + self.target.name + '.extracted'
        self.extracted =  dirname / extracted
        if not self.extracted.exists():
            self.log.warn("\textracted 0 files: {}".format(self.target))
            return None
        else:
            self.log.debug("\textracted path: {}".format(self.extracted))
            return self.extracted
