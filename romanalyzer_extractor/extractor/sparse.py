import os
from pathlib import Path

from romanalyzer_extractor.extractor.ext4img import Ext4ImgExtractor
from romanalyzer_extractor.utils import execute
from romanalyzer_extractor.extractor.base import Extractor
from romanalyzer_extractor.extractor.archive import ArchiveExtractor
from romanalyzer_extractor.extractor.f2fs import F2fsImgExtractor
from romanalyzer_extractor.extractor.erofsimg import ErofsImgExtractor
from romanalyzer_extractor.extractor.extimg import ExtImgExtractor
from romanalyzer_extractor.extractor.ext4img import Ext4ImgExtractor
from romanalyzer_extractor.analysis_extractor.classifier import classify


# known (partially) not working extraction:
# - Realme RMX3521export_11_C.15_2023071017400126.zip
# - Oppo Oppo_Find_X3_Pro_PEEM00_Domestic_11_F.18_230116_QPST.zip https://oppostockrom.com/
class SparseImgExtractor(Extractor):
    def __init__(self, target, target_path=None):
        super().__init__(target, target_path)
        self.tool = Path('romanalyzer_extractor/tools/android-simg2img/simg2img').absolute()

    def extract(self):
        if not self.chmod(): return None

        self.log.debug("sparse image: {}".format(self.target))
        self.log.debug("\tstart convert sparse img to raw img")
        
        if self.target.name.endswith("sparsechunk.0"):
            convert_cmd = '{simg2img} "{sparse_img}".* "{output}"'.format(
                    simg2img=self.tool, 
                    sparse_img=Path(str(self.target).replace("sparsechunk.0", "sparsechunk")),
                    output=Path(str(self.target).replace("_sparsechunk.0", ".raw")))
            execute(convert_cmd)
            raw_img = Path(str(self.target).replace("_sparsechunk.0", ".raw"))
            dir_path = str(self.target.parents[0])
            for file in os.listdir(dir_path):
                if "sparsechunk" in file:
                    os.unlink(os.path.join(dir_path, file))
            if self.target.name.lower().startswith("super."):
                self.target = self.target.parents[0] / "super.img"
        elif self.target.name.startswith("super_"):
            raw_img = self.target.parents[0] / (self.target.name + '.raw')
            convert_cmd = '{simg2img} "{sparse_img}" "{output}"'.format(
                simg2img=self.tool,
                sparse_img=self.target.absolute(),
                output=raw_img)
            execute(convert_cmd)
            self.target.unlink()
            self.log.debug("\tconverted raw image: {}".format(raw_img))
            self.target = self.target.parents[0] / "super.img"
        elif self.target.name.startswith("super.") and os.path.exists(str(self.target.parents[1] / "super_map.csv")):
            self.extracted = self.target.parents[0] / "super.img"
            with open(str(self.target.parents[1] / "super_map.csv")) as f:
                lines = f.readlines()
            super_files = lines[-1].split(",")[-3::]
            super_files[-1] = super_files[-1].replace("\n", "")
            dir_path = str(self.target.parents[0])
            for file in os.listdir(dir_path):
                if file.startswith("super.") and file not in super_files:
                    os.unlink(os.path.join(dir_path, file))
            convert_cmd = '{simg2img} "{super}" "{output}"'.format(
                simg2img=self.tool,
                super=Path(str(self.target.parents[0] / "super.*")),
                output=self.extracted)
            execute(convert_cmd)
            for file in os.listdir(dir_path):
                if file.startswith("super.") and file != "super.img":
                    os.unlink(os.path.join(dir_path, file))
            self.target = self.target.parents[0] / "super.img"
            raw_img = self.target
        elif "sparsechunk" in self.target.name or self.target.name == "userdata.img":
            return None
        else:
            raw_img = self.target.parents[0] / (self.target.name+'.raw')
            convert_cmd = '{simg2img} "{sparse_img}" "{output}"'.format(
                    simg2img=self.tool, 
                    sparse_img=self.target.absolute(), 
                    output=raw_img)
            execute(convert_cmd)
            # if raw_img.exists():
            #     self.target.unlink()
            self.log.debug("\tconverted raw image: {}".format(raw_img))
        if self.target.name.lower() == "super.img":
            self.extracted = []
            for partition in ["system", "vendor", "cust", "odm", "oem", "factory", "product", "xrom", "modem", "dtbo", "dtb", "boot",
                              "recovery", "tz", "systemex", "oppo_product", "preload_common", "system_ext", "system_other", "opproduct"]:  #, reserve india my_preload my_odm my_stock my_operator my_country my_product my_company my_engineering my_heytap my_custom my_manifest my_carrier my_region my_bigball my_version special_preload vendor_dlkm odm_dlkm system_dlkm init_boot vendor_kernel_boot vendor_boot mi_ext boot-debug vendor_boot-debugsuper system vendor cust odm oem factory product xrom modem dtbo dtb boot recovery tz systemex oppo_product preload_common system_ext system_other opproduct reserve india my_preload my_odm my_stock my_operator my_country my_product my_company my_engineering my_heytap my_custom my_manifest my_carrier my_region my_bigball my_version special_preload vendor_dlkm odm_dlkm system_dlkm init_boot vendor_kernel_boot vendor_boot mi_ext boot-debug vendor_boot-debug"):
                convert_cmd = '{lpunpack} --partition="{partition}_a" "{raw_img}" "{output}"'.format(
                    lpunpack=Path('romanalyzer_extractor/tools/lpunpack/lpunpack').absolute(),
                    partition=partition,
                    raw_img=raw_img,
                    output=self.target.parents[0])
                execute(convert_cmd, suppress_output=True)
                convert_cmd = '{lpunpack} --partition="{partition}" "{raw_img}" "{output}"'.format(
                    lpunpack=Path('romanalyzer_extractor/tools/lpunpack/lpunpack').absolute(),
                    partition=partition,
                    raw_img=raw_img,
                    output=self.target.parents[0])
                execute(convert_cmd, suppress_output=True)
                a_img = self.target.parents[0] / (partition + "_a.img")
                img = self.target.parents[0] / (partition + ".img")
                if a_img.exists():
                    a_img.rename(self.target.parents[0] / (partition + ".img"))
                if img.exists():
                    print(f"Found and extracted {partition}.img from super.img.")
                    self.extracted.append(img)
                    self.log.debug("\textracted path: {} from super.img".format(self.extracted[-1]))
            raw_img.unlink()
            return self.extracted

        if not os.access(str(raw_img), os.R_OK):
            self.log.warn("\tNo read permissions for {}".format(raw_img))
            return None
        file_class = classify(raw_img)
        extractor = None
        if file_class == "f2fs":
            extractor = F2fsImgExtractor(raw_img)
        elif file_class == "archive":
            extractor = ArchiveExtractor(raw_img)
        elif file_class == "erofsimg":
            extractor = ErofsImgExtractor(raw_img)
        elif file_class == "extimg":
            extractor = ExtImgExtractor(raw_img)
        elif file_class == "ext4img":
            extractor = Ext4ImgExtractor(raw_img)
        if extractor is not None:
            self.extracted = extractor.extract()

        if self.extracted is None or not self.extracted.exists():
            self.log.warn("\tfailed to extract {}".format(self.target))
            return None
        else:
            self.log.debug("\textracted path: {}".format(self.extracted))
            return self.extracted
