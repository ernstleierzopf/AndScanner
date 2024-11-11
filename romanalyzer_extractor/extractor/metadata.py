import os
import hashlib
import magic
from pathlib import Path
from romanalyzer_extractor.utils import execute
from romanalyzer_extractor.extractor.base import Extractor


class MetadataExtractor(Extractor):
    def extract(self):
        file_metadata_path = os.path.join(self.target_path, "file-metadata.csv")
        if not os.path.exists(file_metadata_path):
            with open(file_metadata_path, "w") as f:
                f.write("Hash;Path;Size;ELF-Build-ID\n")
        with open(file_metadata_path, "a") as f:
            file_type = magic.from_file(str(self.target))
            sha1sum = hashlib.sha1()
            with open(str(self.target), "rb") as fd:
                block = fd.read(2 ** 16)
                while len(block) != 0:
                    sha1sum.update(block)
                    block = fd.read(2 ** 16)
            sha1sum = sha1sum.hexdigest()
            metadata = f"{sha1sum};{str(self.target.absolute()).replace(str(Path(self.target_path).absolute()) + '/', '').replace('.extracted', '').split('/', 1)[1]};{self.target.stat().st_size};"
            if "ELF" in file_type:
                cmd = f'readelf -n "{str(self.target)}"'
                output = execute(cmd, suppress_output=True)
                output_lines = output.split('\n')
                for line in output_lines:
                    line = line.strip()
                    if line.startswith("Build ID: "):
                        metadata += line.replace("Build ID: ", "")
            f.write(metadata+"\n")
