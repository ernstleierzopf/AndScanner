import shutil
import os
from pathlib import Path
from romanalyzer_extractor.utils import execute
from romanalyzer_extractor.extractor.base import Extractor
from romanalyzer_extractor.analysis_extractor.classifier import get_file_type


class ArchiveExtractor(Extractor):

    def extract(self):
        # if not self.chmod(): return None
        self.log.debug("Archive extract target: {}".format(self.target))
        self.log.debug("\tstart extract archive.")

        extract_cmd = ''
        suffix = self.target.suffix
        abspath = self.target.absolute()

        if self.target.stat().st_size == 0:
            self.log.warn("\tthis is a empty archive {}".format(self.target))
            return None

        if suffix == '':
            mime = get_file_type(abspath, True)
            if mime == 'application/x-lz4':
                suffix = '.lz4'
            elif mime == 'application/gzip':
                suffix = '.gz'
                new_path = Path(f'{abspath}.extracted{suffix}')
                self.extracted = Path(f'{self.target}.extracted')
                shutil.copy(abspath, new_path)
                abspath = new_path
                self.target = abspath
            elif mime == 'application/octet-stream' and self.target.name == "kernel":
                cmd = 'binwalk "{}" '.format(self.target)
                output = execute(cmd, suppress_output=True)
                skip = True
                firstline = False
                for line in output.split("\n"):
                    if line.startswith("-------------"):
                        skip = False
                        firstline = True
                        continue
                    if skip:
                        continue
                    if firstline:
                        if "Linux kernel ARM boot executable" not in line:
                            self.log.warn(f"\tfailed to extract {self.target}. No 'Linux kernel ARM boot executable' string in first line. line: {line}")
                            return None
                        firstline = False
                    else:
                        if "gzip compressed data" in line or "LZMA compressed data" in line:
                            if "gzip compressed data" in line:
                                suffix = ".gz"
                            else:
                                suffix = ".lzma"
                            data = line.split()
                            _decimal = int(data[0])
                            hex_offset = data[1]
                            _description = " ".join(data[2:])
                            abspath = Path(f'{self.target}.extracted{suffix}')
                            self.extracted = Path(f'{self.target}.extracted')
                            cmd = 'dd if="{}" bs=1 skip=$(({})) of="{}"'.format(self.target, hex_offset, abspath)
                            self.target = abspath
                            execute(cmd, suppress_output=True)
                            break
            self.log.info(f'\tfound suffix {suffix} for {abspath}.')

        if suffix in ('.tar.gz', '.tgz'):
            extract_cmd = 'mkdir "{}"'.format(self.extracted)
            extract_cmd = extract_cmd+' && tar -zxf "{}" -C "{}"'.format(abspath, self.extracted)
        elif suffix == '.gz':
            extract_cmd = 'gunzip -f -d "{}"'.format(abspath)
            self.extracted = self.target.with_suffix('')
        # elif suffix == '.zip':
        #     extract_cmd = 'unzip -P x -o "{}" -d "{}"'.format(abspath, self.extracted)
        elif suffix == '.rar':
            extract_cmd = 'unrar -px  x "{}" "{}/" -y'.format(abspath, self.extracted)
        elif suffix in ('.7z', '.zip', '.ext4', '.rar', '.ftf', '.lzma'):
            extract_cmd = '7z -pfotatest1234 x "{}" -o"{}" -y'.format(abspath, self.extracted)
        elif suffix == ".raw":
            extract_cmd = '7z -p x "{}" -o"{}" -y'.format(abspath, self.extracted)
        elif suffix == '.md5':
            if self.target.name.endswith('tar.md5'):
                extract_cmd = 'mkdir "{}"'.format(self.extracted)
                extract_cmd = extract_cmd+' && tar -xf "{}" -C "{}"'.format(abspath, self.extracted)
            else:
                return None
        elif suffix == '.img':
            extract_cmd = 'mkdir "{}"'.format(self.extracted)
            extract_cmd = extract_cmd + ' && tar -xf "{}" -C "{}"'.format(abspath, self.extracted)
        elif suffix == '.APP' and str(abspath).find("UPDATE.APP") != -1:
            extract_cmd = 'perl romanalyzer_extractor/tools/huawei_erofs/split_updata.pl "{}" "{}"'.format(abspath, self.extracted)
        elif suffix == '.lz4':
            extract_cmd = 'lz4 -f -d "{}" "{}"'.format(abspath, self.extracted)
        else:
            return None

        output, exit_code = execute(extract_cmd, return_exit_code=True, redirect_stderr_stdout=True)

        if not self.extracted.exists():
            self.log.warn("\tfailed to extract {}".format(self.target))
            if not exit_code:
                self.log.error(output)
            return None
        else:
            self.log.debug("\textracted path: {}".format(self.extracted))
            if not self.is_base_file and abspath.exists():
                abspath.unlink()
            return self.extracted
