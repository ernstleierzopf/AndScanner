from pathlib import Path

from romanalyzer_extractor.extractor.base import Extractor
from romanalyzer_extractor.utils import execute


class AndrOtaPayloadExtractor(Extractor):
    def __init__(self, target, target_path=None):
        super().__init__(target, target_path)
        self.tool = Path('romanalyzer_extractor/tools/extract_android_ota_payload/extract_android_ota_payload.py').absolute()

    def extract(self):
        self.log.debug(f"Android OTA Payload extract target: {self.target}")
        self.log.debug("\tstart extract payload.bin.")

        # Extraction command parts.
        payload = self.target.absolute()
        extracted_dir = self.extracted

        # Build extraction command.
        convert_cmd = f"python3 {self.tool} \"{payload}\" \"{extracted_dir}\""

        # Extract OTA image.
        execute(convert_cmd)

        if self.extracted.exists():
            self.log.debug(f"\textracted ota payload.bin to: {self.extracted}")
            payload.unlink()
        else:
            self.log.warning(f"\tfailed to extract {self.extracted} using unzip")
            return None

        # # Extract nested files.
        # for file in self.target.glob("**/*"):
        #     ROMExtractor(file).extract()

        return self.extracted
