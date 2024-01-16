from pathlib import Path

from romanalyzer_extractor.analysis_extractor.classifier import classify

from romanalyzer_extractor.extractor.base import Extractor
from romanalyzer_extractor.extractor.archive import ArchiveExtractor
from romanalyzer_extractor.extractor.binwalk import BinwalkExtractor
from romanalyzer_extractor.extractor.bootimg import BootImgExtractor
from romanalyzer_extractor.extractor.brotli import BrotliExtractor
from romanalyzer_extractor.extractor.extimg import ExtImgExtractor
from romanalyzer_extractor.extractor.newdat import NewDatExtractor
from romanalyzer_extractor.extractor.ota import AndrOtaPayloadExtractor
from romanalyzer_extractor.extractor.ozip import OZipExtractor
from romanalyzer_extractor.extractor.sparse import SparseImgExtractor
from romanalyzer_extractor.extractor.dir import DirExtractor
from romanalyzer_extractor.extractor.ofp import OfpExtractor


class ROMExtractor(Extractor):

    process_queue = []

    extractor_map = {
        'ozip': OZipExtractor,
        'archive': ArchiveExtractor,
        'otapayload': AndrOtaPayloadExtractor,
        'bootimg': BootImgExtractor,
        # 'binwalk': BinwalkExtractor,
        'sparseimg': SparseImgExtractor,
        'extimg': ExtImgExtractor,
        'brotli': BrotliExtractor,
        'newdat': NewDatExtractor,
        'dir': DirExtractor,
        'ofp': OfpExtractor
    }

    def enqueue(self, target):
        if isinstance(target, list): 
            self.process_queue.extend(target)
        elif isinstance(target, Path): 
            self.process_queue.append(target)

    def extract(self):
        self.log.debug('add {} to process queue'.format(self.target))
        self.process_queue.append(self.target)
        
        while self.process_queue:
            
            process_item = self.process_queue.pop()
            guess = classify(process_item)
            
            self.log.debug("\t 000000 {}  {}".format(process_item, guess))
            
            if guess not in self.extractor_map.keys():
                continue

            try:
                print(guess)
                self.enqueue(self.extractor_map[guess](process_item).extract())
            except Exception as e:
                self.log.exception("failed to extract {} ... skip it.".format(process_item))
                self.log.exception(e)

        if not self.extracted.exists():
            self.log.debug("Failed to extract: {}".format(self.extracted))
            return None
        else:
            self.log.debug("Extracted path: {}".format(self.extracted))
            return self.extracted
