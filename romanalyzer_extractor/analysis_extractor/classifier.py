import magic
from pathlib import Path
from romanalyzer_extractor.utils import log

EXT_EXT = ('ext2', 'ext3', 'ext4')
ARCHIVE_EXT = ('.gz', '.tgz', '.bz2', '.xz', '.tar', '.zip', '.rar', '.7z','.md5','.APP','.lz4')
INTERESTING_EXT = ('.ko', '.so', '.dex', '.odex', '.apk', '.jar', '.ozip', '.apex', '.vdex')


def get_file_type(target: Path, mime=False):
    if target.is_dir():
        return "dir"
    else:
        return magic.from_file(str(target), mime=mime)


def classify(target):
    # Initialize Path object.
    target = Path(target)

    if not target.exists():
        if not target.is_symlink() and not target.name.startswith("super."):  # allow broken symlinks
            log.warn(f"Target path does not exist: {target}")
        return None

    # Get the file system description using the python-magic.
    file_type = get_file_type(target)
    file_mime_type = get_file_type(target, mime=True)

    # *** Start Checks ***

    # dir
    if target.is_dir():
        return "dir"

    # symlink
    if target.is_symlink():
        return "symlink"

    if target.name == "vbmeta.img":
        return "vbmeta"

    # new dat
    if target.name.endswith('.new.dat'):
        return 'newdat'

    if target.name.split('.')[-1].isnumeric() and target.name.endswith('.new.dat.' + target.name.split('.')[-1]):
        return 'data'

    # br
    if target.name.endswith('.new.dat.br'):
        return 'brotli'

    # interesting extensions.
    if target.suffix in INTERESTING_EXT:
        return target.suffix.strip('.')

    # archive file
    if target.suffix in ARCHIVE_EXT or file_mime_type == 'application/zip':
        return "archive"

    # special types.
    if file_type == "data":
        if target.name == 'payload.bin':
            return 'otapayload'

        if target.suffix in ('.img', '.raw'):  # just try extracting as EROFS fs - better than doing nothing.  # and 'UPDATE.APP' in str(target):
            return 'erofsimg'

        if target.suffix in ('.img', '.bin', '.raw'):
            return 'dataimg'

        if target.suffix == '.pac':
            return 'pac'

        else:
            return 'data'

    if "F2FS" in file_type:
        return "f2fs"

    # elf
    if "ELF" in file_type:
        return "elf"

    if "EROFS" in file_type:
        return "erofsimg"

    # ascii
    if "ASCII" in file_type:
        return "text"

    # Android boot img
    if "Android bootimg" in file_type:
        return "bootimg"

    # Android Sparse img
    if "Android sparse image" in file_type:
        return "sparseimg"

    # ext2/3/4 filesystem
    if any(ext in file_type for ext in EXT_EXT):
        return "extimg"

    if file_type == "OpenPGP Public Key":
        return "ofp"

    return 'unknown'
