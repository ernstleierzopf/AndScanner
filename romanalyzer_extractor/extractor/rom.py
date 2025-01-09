import os
from pathlib import Path

from romanalyzer_extractor.analysis_extractor.classifier import classify
from romanalyzer_extractor.utils import execute

from romanalyzer_extractor.extractor.base import Extractor
from romanalyzer_extractor.extractor.archive import ArchiveExtractor
from romanalyzer_extractor.extractor.bootimg import BootImgExtractor
from romanalyzer_extractor.extractor.brotli import BrotliExtractor
from romanalyzer_extractor.extractor.extimg import ExtImgExtractor
from romanalyzer_extractor.extractor.ext4img import Ext4ImgExtractor
from romanalyzer_extractor.extractor.newdat import NewDatExtractor
from romanalyzer_extractor.extractor.ota import AndrOtaPayloadExtractor
from romanalyzer_extractor.extractor.ozip import OZipExtractor
from romanalyzer_extractor.extractor.sparse import SparseImgExtractor
from romanalyzer_extractor.extractor.dir import DirExtractor
from romanalyzer_extractor.extractor.ofp import OfpExtractor
from romanalyzer_extractor.extractor.f2fs import F2fsImgExtractor
from romanalyzer_extractor.extractor.pac import PacExtractor
from romanalyzer_extractor.extractor.erofsimg import ErofsImgExtractor
from romanalyzer_extractor.extractor.metadata import MetadataExtractor
from romanalyzer_extractor.extractor.sonyimg import SonyImgExtractor


class ROMExtractor(Extractor):
    def __init__(self, target, target_path=None):
        super().__init__(target, target_path)
        self.avbtool = Path("romanalyzer_extractor/tools/vbmeta/avbtool.py").absolute()
        self.fbpacktool = Path("romanalyzer_extractor/tools/vbmeta/fbpacktool.py").absolute()

        self.process_queue = []
        self.partition_paths = []
        self.bootloader_img = None
        self.vbmeta_img = None

        self.extractor_map = {
            'ozip': OZipExtractor,
            'archive': ArchiveExtractor,
            'otapayload': AndrOtaPayloadExtractor,
            'bootimg': BootImgExtractor,
            # 'binwalk': BinwalkExtractor,
            'sparseimg': SparseImgExtractor,
            'extimg': ExtImgExtractor,
            'ext4img': Ext4ImgExtractor,
            'brotli': BrotliExtractor,
            'newdat': NewDatExtractor,
            'dir': DirExtractor,
            'ofp': OfpExtractor,
            'f2fs': F2fsImgExtractor,
            'pac': PacExtractor,
            'erofsimg': ErofsImgExtractor,
            'sonyimg': SonyImgExtractor,
            'elf': MetadataExtractor, 'ko': MetadataExtractor, 'so': MetadataExtractor, 'dex': MetadataExtractor, 'odex': MetadataExtractor,
            'apk': MetadataExtractor, 'jar': MetadataExtractor, 'apex': MetadataExtractor, 'vdex': MetadataExtractor
        }

    def enqueue(self, target):
        if target is None:
            return
        if isinstance(target, Path):
            target = [target]
        for item in target:
            abspath = item.absolute()
            if abspath.name.lower().startswith("bootloader") and abspath.name.lower().endswith(".img"):
                cnt = 0
                for i in self.process_queue:
                    if i.name.lower().startswith("bootloader") and i.name.lower().endswith(".img"):
                        cnt += 1
                if cnt == 1:
                    self.bootloader_img = abspath
                    target.remove(item)
            elif abspath.name.lower() in ("boot.img", "recovery.img", "system.img", "dtbo.img", "vendor.img", "vbmeta_system.img",
                                          "vbmeta_vendor.img"):
                self.partition_paths.append(abspath)
            elif abspath.name.lower() == "vbmeta.img":
                self.vbmeta_img = abspath
            elif abspath.name.lower() == "vbmeta-sign.img":
                self.vbmeta_img = abspath
            elif abspath.name.lower() == "vbmeta.bin":
                self.vbmeta_img = abspath
        self.process_queue.extend(target)

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
                if guess not in ('ko', 'so', 'dex', 'odex', 'apk', 'jar', 'apex', 'vdex', 'elf'):
                    print(guess)
                extractor = self.extractor_map[guess](process_item, self.target_path)
                if is_base_file:
                    extractor.is_base_file = True
                    is_base_file = False
                self.enqueue(extractor.extract())
            except Exception as e:
                self.log.exception("failed to extract {} ... skip it.".format(process_item))
                self.log.exception(e)
        if self.vbmeta_img is not None:
            self.prepare_vbmeta()
            self.rename_missing_vbmeta_files()
            success = self.verify_vbmeta()
            self.extract_vbmeta_digests(success)
        else:
            keys = ["image"]
            digests = [self.target.name]
            with open(os.path.join(self.target_path, "vbmeta-digests.csv"), "w") as f:
                f.write(";".join(keys) + "\n")
                f.write(";".join(digests) + "\n")

        if not self.extracted.exists():
            self.log.debug("Failed to extract: {}".format(self.extracted))
            return None
        else:
            self.log.debug("Extracted path: {}".format(self.extracted))
            return self.extracted

    def prepare_vbmeta(self):
        for part in self.partition_paths:
            if self.vbmeta_img.parents[0] != part.parents[0] and not os.path.exists(str(self.vbmeta_img.parents[0] / part.name)):
                link = self.vbmeta_img.parents[0] / part.name
                link.symlink_to(part)
        if self.bootloader_img is not None:
            # Build bootloader extraction command.
            extract_bootloader_cmd = f"python3 {self.fbpacktool} unpack \"{self.bootloader_img}\" -o \"{str(self.vbmeta_img.parent)}\""
            # Perform bootloader extraction.
            output, exit_code = execute(extract_bootloader_cmd, return_exit_code=True)
            if exit_code != 0:
                self.log.debug("Failed to extract: {}".format(self.bootloader_img))
            else:
                self.log.debug("\textracted bootloader image {} to {}.".format(self.bootloader_img, str(self.vbmeta_img.parent)))
        # Build vbmeta digest extraction command.
        # to prevent "Given image does not look like a vbmeta image" in avbtool.py
        # https://www.hovatek.com/forum/thread-32666-post-194924.html#pid194924
        with open(self.vbmeta_img, "rb") as f:
            data = f.read()
        pos = data.find(b'AVB0')
        if pos != 0:
            with open(self.vbmeta_img, "wb") as f:
                f.write(data[pos:])

    def extract_vbmeta_digests(self, verified):
        vbmeta_digest_extraction_cmd = f"python3 {self.avbtool} calculate_vbmeta_digest --image \"{self.vbmeta_img}\""
        output, exit_code = execute(vbmeta_digest_extraction_cmd, return_exit_code=True, suppress_output=True)
        keys = ["image", "vbmeta", "verified"]
        if exit_code != 0:
            output = "missing partitions"
        digests = [self.target.name, output.replace("\n", "").strip(), "0" if verified else "1"]
        vbmeta_digest_extraction_cmd = f"python3 {self.avbtool} print_partition_digests --image \"{self.vbmeta_img}\""
        output = execute(vbmeta_digest_extraction_cmd)
        for line in output.split("\n"):
            if line == "":
                continue
            key, digest = line.split(":")
            keys.append(key)
            digests.append(digest.replace("\n", "").strip())
        with open(os.path.join(self.target_path, "vbmeta-digests.csv"), "w") as f:
            f.write(";".join(keys) + "\n")
            f.write(";".join(digests) + "\n")
        self.log.debug("\tstored digests in {}".format(os.path.join(self.target_path, "vbmeta-digests.csv")))

    def verify_vbmeta(self):
        # if .img files are not found, they are skipped. But as long all found img files can be verified, verification succeeds.
        verify_vbmeta_cmd = f"python3 {self.avbtool} verify_image --image \"{self.vbmeta_img}\" --follow_chain_partitions --allow_missing_partitions"
        output, exit_code = execute(verify_vbmeta_cmd, return_exit_code=True, redirect_stderr_stdout=True)
        self.log.debug("vbmeta output: " + output)
        if exit_code != 0:
            # known issue with Huawei vbmeta verification: https://github.com/berkeley-dev/huawei_quirks
            # None of the Vivo firmware images from https://www.vivo.com/uk/support/system-update can be verified
            self.log.debug("Failed to verify image with vbmeta.img.")
            return False
        self.log.debug("\tverified image with vbmeta.img successfully.")
        return True

    def rename_missing_vbmeta_files(self):
        vbmeta_digest_extraction_cmd = f"python3 {self.avbtool} print_partition_digests --image \"{self.vbmeta_img}\""
        output = execute(vbmeta_digest_extraction_cmd)
        for line in output.split("\n"):
            if line == "":
                continue
            key, digest = line.split(":")
            if digest.strip() == "missing":
                for file in os.listdir(os.path.dirname(self.vbmeta_img)):
                    if file.endswith(".raw") or file.endswith(".extracted"):
                        continue
                    basename, extension = os.path.splitext(file)
                    if key[:16].lower() == basename.lower():
                        if basename.isupper():
                            newfile = os.path.join(os.path.dirname(self.vbmeta_img), key.upper() + extension)
                            os.rename(os.path.join(os.path.dirname(self.vbmeta_img), file), newfile)
                        else:
                            newfile = os.path.join(os.path.dirname(self.vbmeta_img), key + extension)
                            os.rename(os.path.join(os.path.dirname(self.vbmeta_img), file), newfile)
                        self.log.debug("renamed " + file + " to " + os.path.basename(newfile))
