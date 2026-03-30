#!/usr/bin/env python3
"""
Unpacks Android boot, recovery, and vendor_boot images safely.

Automatically detects page size and decodes string fields safely.
"""

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from struct import unpack
import os
import shlex

VENDOR_RAMDISK_NAME_SIZE = 32
VENDOR_RAMDISK_TABLE_ENTRY_BOARD_ID_SIZE = 16


def create_out_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def extract_image(offset, size, bootimage, extracted_image_name):
    bootimage.seek(offset)
    with open(extracted_image_name, 'wb') as file_out:
        file_out.write(bootimage.read(size))


def get_number_of_pages(image_size, page_size):
    return (image_size + page_size - 1) // page_size


def cstr(b):
    """Remove NULL bytes and decode safely."""
    if isinstance(b, bytes):
        return b.split(b'\0', 1)[0].decode(errors='ignore')
    return str(b).split('\0', 1)[0]


def format_os_version(os_version):
    if os_version == 0:
        return None
    a = os_version >> 14
    b = (os_version >> 7) & ((1 << 7) - 1)
    c = os_version & ((1 << 7) - 1)
    return f'{a}.{b}.{c}'


def format_os_patch_level(os_patch_level):
    if os_patch_level == 0:
        return None
    y = (os_patch_level >> 4) + 2000
    m = os_patch_level & 0xF
    return f'{y:04d}-{m:02d}'


def decode_os_version_patch_level(os_version_patch_level):
    os_version = os_version_patch_level >> 11
    os_patch_level = os_version_patch_level & ((1 << 11) - 1)
    return format_os_version(os_version), format_os_patch_level(os_patch_level)


class BootImageInfoFormatter:
    """Formats the boot image info."""

    def format_pretty_text(self):
        lines = []
        lines.append(f'boot magic: {self.boot_magic}')
        lines.append(f'header version: {self.header_version}')
        lines.append(f'page size: {self.page_size}')
        lines.append(f'kernel size: {self.kernel_size}')
        lines.append(f'ramdisk size: {self.ramdisk_size}')
        if self.header_version < 3:
            lines.append(f'second bootloader size: {self.second_size}')
            lines.append(f'kernel load address: {self.kernel_load_address:#010x}')
            lines.append(f'ramdisk load address: {self.ramdisk_load_address:#010x}')
            lines.append(f'second load address: {self.second_load_address:#010x}')
            lines.append(f'tags load address: {self.tags_load_address:#010x}')
            lines.append(f'product name: {self.product_name}')
        lines.append(f'os version: {self.os_version}')
        lines.append(f'os patch level: {self.os_patch_level}')
        lines.append(f'cmdline: {self.cmdline}')
        if self.header_version < 3:
            lines.append(f'extra cmdline: {self.extra_cmdline}')
        return '\n'.join(lines)


def unpack_boot_image(boot_img, output_dir):
    info = BootImageInfoFormatter()

    # Read boot magic
    boot_img.seek(0)
    info.boot_magic = unpack('8s', boot_img.read(8))[0].decode(errors='ignore')

    # Detect page size from header
    boot_img.seek(36)
    info.page_size = unpack('I', boot_img.read(4))[0]

    # Move to kernel/ramdisk/second info
    boot_img.seek(8)
    kernel_ramdisk_second_info = unpack('9I', boot_img.read(36))
    info.header_version = kernel_ramdisk_second_info[8]

    if info.header_version < 3:
        info.kernel_size = kernel_ramdisk_second_info[0]
        info.kernel_load_address = kernel_ramdisk_second_info[1]
        info.ramdisk_size = kernel_ramdisk_second_info[2]
        info.ramdisk_load_address = kernel_ramdisk_second_info[3]
        info.second_size = kernel_ramdisk_second_info[4]
        info.second_load_address = kernel_ramdisk_second_info[5]
        info.tags_load_address = kernel_ramdisk_second_info[6]
        os_version_patch_level = unpack('I', boot_img.read(4))[0]
    else:
        info.kernel_size = kernel_ramdisk_second_info[0]
        info.ramdisk_size = kernel_ramdisk_second_info[1]
        os_version_patch_level = kernel_ramdisk_second_info[2]
        info.second_size = 0

    info.os_version, info.os_patch_level = decode_os_version_patch_level(os_version_patch_level)

    if info.header_version < 3:
        info.product_name = cstr(unpack('16s', boot_img.read(16))[0])
        info.cmdline = cstr(unpack('512s', boot_img.read(512))[0])
        boot_img.read(32)  # ignore SHA
        info.extra_cmdline = cstr(unpack('1024s', boot_img.read(1024))[0])
    else:
        info.cmdline = cstr(unpack(f'{info.page_size - 512}s', boot_img.read(info.page_size - 512))[0])

    # Extract kernel, ramdisk, second
    num_header_pages = 1
    page_size = info.page_size

    num_kernel_pages = get_number_of_pages(info.kernel_size, page_size)
    kernel_offset = page_size * num_header_pages
    num_ramdisk_pages = get_number_of_pages(info.ramdisk_size, page_size)
    ramdisk_offset = page_size * (num_header_pages + num_kernel_pages)

    image_info_list = [
        (kernel_offset, info.kernel_size, 'kernel'),
        (ramdisk_offset, info.ramdisk_size, 'ramdisk')
    ]

    if info.second_size > 0:
        second_offset = page_size * (num_header_pages + num_kernel_pages + num_ramdisk_pages)
        image_info_list.append((second_offset, info.second_size, 'second'))

    create_out_dir(output_dir)
    for offset, size, name in image_info_list:
        extract_image(offset, size, boot_img, os.path.join(output_dir, name))

    info.image_dir = output_dir
    return info


def unpack_bootimg(boot_img_path, output_dir):
    with open(boot_img_path, 'rb') as boot_img:
        boot_img.seek(0)
        magic = unpack('8s', boot_img.read(8))[0].decode(errors='ignore')
        boot_img.seek(0)
        if magic == 'ANDROID!':
            return unpack_boot_image(boot_img, output_dir)
        else:
            raise ValueError(f'Not a recognized Android boot image, magic={magic}')


def parse_cmdline():
    parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
        description='Unpacks Android boot/recovery/vendor_boot image.',
    )
    parser.add_argument('--boot_img', required=True, help='Path to boot/recovery/vendor_boot image')
    parser.add_argument('--out', default='out', help='Output directory')
    return parser.parse_args()


def main():
    args = parse_cmdline()
    info = unpack_bootimg(args.boot_img, args.out)
    print(info.format_pretty_text())


if __name__ == '__main__':
    main()

