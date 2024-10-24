import os
from pathlib import Path
from romanalyzer_extractor.utils import execute
from romanalyzer_extractor.extractor.base import Extractor
from romanalyzer_extractor.extractor.extimg import ExtImgExtractor


class NewDatExtractor(Extractor):
    def __init__(self, target, target_path=None):
        super().__init__(target, target_path)
        self.tool = Path('romanalyzer_extractor/tools/sdat2img/sdat2img.py').absolute()

    def extract(self):
        self.log.debug("New.dat extract: {}".format(self.target))
        workdir = self.target.parents[0]
        merged_target = workdir / "{}".format('merged_' + self.target.name)
        target_files = []
        dir_path = str(self.target.parents[0])
        for file in sorted(os.listdir(dir_path)):
            if file.startswith(self.target.name) and (file == self.target.name or (file.split(".")[-1].isnumeric() and file == self.target.name + "." + file.split(".")[-1])):
                target_files.append(os.path.join(dir_path, file))
        target_files = target_files[0] + " " + " ".join(sorted(target_files[1:], key=lambda x: int(x.split(".")[-1])))
        merge_cmd = 'cat {target} > {merged_target}'.format(target=target_files.strip(), merged_target=merged_target)
        execute(merge_cmd)

        transfer_list = workdir / "{}".format(self.target.name.replace('.new.dat', '.transfer.list'))

        if not transfer_list.exists():
            self.log.warn("cannot unpack {} because lack of {}".format(self.target, transfer_list))
            return None

        output_system_img = workdir / "{}".format(self.target.name.replace('.new.dat', '.img'))

        convert_cmd = 'python3 {sdat2img} "{transfer_list}" "{system_new_file}" "{system_img}"'.format(
            sdat2img=self.tool, transfer_list=transfer_list, system_new_file=merged_target, system_img=output_system_img
        )
        execute(convert_cmd)

        if merged_target.stat().st_size != output_system_img.stat().st_size:
            self.log.warn("\tmerged file size does not match output file size (file: {}, expected: {}, actual: {} merged files: {})".format(
                self.target, merged_target.stat().st_size, output_system_img.stat().st_size, target_files))
        merged_target.unlink()
        dir_path = str(self.target.parents[0])
        for file in os.listdir(dir_path):
            if file.startswith(self.target.name) and (file == self.target.name or (file.endswith('.new.dat.' + file.split('.')[-1]) and file.split('.')[-1].isnumeric())):
                os.unlink(os.path.join(dir_path, file))

        extractor = ExtImgExtractor(output_system_img)
        self.extracted = extractor.extract()
        if self.extracted and self.extracted.exists():
            self.log.debug("\textracted path: {}".format(self.extracted))
            return self.extracted
        else:
            self.log.warn("\tfailed to extract {}".format(self.target))
            return None
