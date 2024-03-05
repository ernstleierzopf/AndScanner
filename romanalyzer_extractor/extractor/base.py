import logging
from pathlib import Path
from romanalyzer_extractor.utils import execute


def initialize_attributes(target, target_path):
    _target = None
    _extracted = None

    # Target Path
    _target = Path(target).absolute()

    # Extracted Path
    if _target.suffix == '.ozip':
        local_extract = _target.with_suffix('.zip').name + '.extracted'
    elif _target.name.endswith('.img.lz4'):
        local_extract = _target.name.replace('.img.lz4', '.img')
    elif _target.name.endswith('.bin.lz4'):
        local_extract = _target.name.replace('.bin.lz4', '.bin')
    else:
        local_extract = _target.name + '.extracted'

    _extracted = _target.parent / local_extract
    if target_path is not None and not str(_extracted).startswith(target_path):
        _extracted = Path(target_path).absolute() / local_extract

    return _target, _extracted


class Extractor(object):
    def __init__(self, target, target_path=None):
        self.target_path = target_path
        self.target, self.extracted = initialize_attributes(target, target_path)
        self.tool = Path()
        self.log = logging.getLogger('extractor')
        self.is_base_file = False

    def extract(self):
        raise NotImplementedError

    def chmod(self):
        if not self.tool.exists():
            self.log.error(f"Failed to find extraction tool: {self.tool}")
            return False

        # Build chmod command.
        chmod_cmd = f"chmod +x {self.tool}"

        # Perform chmod command.
        execute(chmod_cmd)

        return True
