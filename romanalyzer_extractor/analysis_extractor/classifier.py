import magic
from pathlib import Path
from romanalyzer_extractor.utils import log

EXT_EXT = ('ext2', 'ext3', 'ext4')
ARCHIVE_EXT = ('.gz', '.tgz', '.bz2', '.xz', '.tar', '.zip', '.rar', '.7z','.md5','.APP')
INTERESTING_EXT = ('.ko', '.so', '.dex', '.odex', '.apk', '.jar', '.ozip')


def get_file_type(target: Path, mime=False):
    if target.is_dir():
        return "dir"
    else:
        return magic.from_file(str(target), mime=mime)


def classify(target):
    # Initialize Path object.
    target = Path(target)

    if not target.exists():
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

    # new dat
    if target.name.endswith('.new.dat'):
        return 'newdat'

    # br
    if target.name.endswith('.new.dat.br'):
        return 'brotli'

    # archive file
    if target.suffix in ARCHIVE_EXT or file_mime_type == 'application/zip':
        return "archive"

    # ext2/3/4 filesystem
    if any(ext in file_type for ext in EXT_EXT):
        return "extimg"

    # Android Sparse img
    if "Android sparse image" in file_type:
        return "sparseimg"

    # Android boot img
    if "Android bootimg" in file_type:
        return "bootimg"

    # elf
    if "ELF" in file_type:
        return "elf"

    # ascii
    if "ASCII" in file_type:
        return "text"

    # special types.
    if target.name == 'payload.bin':
        return 'otapayload'

    if target.suffix in ('.img', '.bin'):
        return 'dataimg'

    if file_type == "data":
        return 'data'

    # interesting extensions.
    if target.suffix in INTERESTING_EXT:
        return target.suffix.strip('.')

    return 'unknown'
