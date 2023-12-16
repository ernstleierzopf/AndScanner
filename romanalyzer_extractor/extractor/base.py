import logging
from pathlib import Path
from romanalyzer_extractor.utils import execute


def initialize_attributes(target):
    _target = None
    _extracted = None

    # Target Path
    if isinstance(target, Path):
        _target = target
    else:
        _target = Path(target).absolute()

    # Extracted Path
    if _target.suffix == '.ozip':
        local_extract = _target.with_suffix('.zip').name + '.extracted'
    else:
        local_extract = _target.name + '.extracted'

    _extracted = _target.parent / local_extract

    return _target, _extracted


class Extractor(object):
    def __init__(self, target):
        self.target, self.extracted = initialize_attributes(target)
        self.tool = Path()
        self.log = logging.getLogger('extractor')

    def extract(self):
        raise NotImplementedError

    def chmod(self):
        if not self.tool.exists():
            self.log.error(f"Failed to found {self.tool}")
            return False
        
        chmod_cmd = 'chmod +x "{tool}"'.format(tool=self.tool)
        execute(chmod_cmd)

        return True
