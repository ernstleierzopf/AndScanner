import subprocess
import shutil
import os
from pathlib import Path
from romanalyzer_extractor.utils import execute
from romanalyzer_extractor.extractor.base import Extractor
from romanalyzer_extractor.extractor.archive import ArchiveExtractor


class F2fsImgExtractor(Extractor):
    def extract(self):
        if not self.chmod(): return None
        abspath = self.target.absolute()
        mount_point = f"/tmp/{self.target.name}.mounted"
        mount_cmd = 'mount -t f2fs "{f2fs_img}" "{mount_point}"'.format(
            f2fs_img=self.target,
            mount_point=mount_point)
        umount_cmd = 'umount "{mount_point}"'.format(
            mount_point=mount_point)
        if os.getuid() != 0:  # non-root user
            self.log.debug("\tpython script not running as root. Adding sudo to mount command.")
            mount_cmd = "sudo " + mount_cmd
            umount_cmd = "sudo " + umount_cmd
        try:
            os.mkdir(mount_point)
            subprocess.check_call(mount_cmd, shell=True, encoding='utf-8')
            try:
                shutil.copytree(mount_point, self.extracted)
            except shutil.Error as e:
                self.log.debug(f"Encountered errors when copying files from {mount_point}")
                self.log.debug(e)
            subprocess.check_call(umount_cmd, shell=True, encoding='utf-8')
            shutil.rmtree(mount_point)
            if abspath.exists():
                abspath.unlink()
        except subprocess.CalledProcessError as e:
            self.log.error(f"Could not mount {self.target} to {mount_point}. Skipping {self.target}..")
            self.log.exception(e)

        if self.extracted is None or not self.extracted.exists():
            self.log.warn("\tfailed to extract {}".format(self.target))
            return None
        else:
            self.log.debug("\textracted path: {}".format(self.extracted))
            return self.extracted
