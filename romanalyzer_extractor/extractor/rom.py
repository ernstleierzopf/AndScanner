import os
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
from romanalyzer_extractor.extractor.f2fs import F2fsImgExtractor
from romanalyzer_extractor.extractor.pac import PacExtractor
from romanalyzer_extractor.extractor.erofsimg import ErofsImgExtractor


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
        'ofp': OfpExtractor,
        'f2fs': F2fsImgExtractor,
        'pac': PacExtractor,
        'erofsimg': ErofsImgExtractor
    }

    def enqueue(self, target):
        if isinstance(target, list): 
            self.process_queue.extend(target)
        elif isinstance(target, Path): 
            self.process_queue.append(target)

    def extract(self):
        self.log.debug('add {} to process queue'.format(self.target))
        self.process_queue.append(self.target)

        is_base_file = True
        while self.process_queue:
            
            process_item = self.process_queue.pop()
            if not os.access(process_item, os.R_OK):
                self.log.warn("\tNo read permissions for {}".format(process_item))
                continue
            guess = classify(process_item)
            
            self.log.debug("\t 000000 {}  {}".format(process_item, guess))
            
            if guess not in self.extractor_map.keys():
                continue

            try:
                print(guess)
                extractor = self.extractor_map[guess](process_item, self.target_path)
                if is_base_file:
                    extractor.is_base_file = True
                    is_base_file = False
                self.enqueue(extractor.extract())
            except Exception as e:
                self.log.exception("failed to extract {} ... skip it.".format(process_item))
                self.log.exception(e)

        if not self.extracted.exists():
            self.log.debug("Failed to extract: {}".format(self.extracted))
            return None
        else:
            self.log.debug("Extracted path: {}".format(self.extracted))
            return self.extracted
