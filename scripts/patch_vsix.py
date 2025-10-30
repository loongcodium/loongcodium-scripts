# /// script
# dependencies = [
#     "lxml",
# ]
# ///
import shutil
from argparse import ArgumentParser
from glob import glob
from tempfile import mkstemp
from zipfile import ZipFile

from lxml import etree


def get_args():
    parser = ArgumentParser()
    parser.add_argument(
        "vsix_files",
        nargs="*",
        default=glob("*.vsix"),
        help="path to `.vsix` files. default: `./*.vsix`",
    )
    parser.add_argument(
        "-t", "--target_platform", default="linux-loong64", help="default: %(default)s"
    )
    return parser.parse_args()


def update_target(vsixmanifest: bytes, target_platform: str):
    tree = etree.fromstring(
        vsixmanifest, parser=etree.XMLParser(remove_blank_text=False)
    )

    tree.find(
        ".//vsx:Identity",
        {"vsx": "http://schemas.microsoft.com/developer/vsx-schema/2011"},
    ).set("TargetPlatform", target_platform)

    return etree.tostring(
        tree, xml_declaration=True, encoding="utf-8", pretty_print=False
    )


def patch_vsix(vsix_file, target_platform):
    temp_vsix_path = mkstemp()[1]
    with (
        ZipFile(vsix_file, "r") as source_vsix,
        ZipFile(temp_vsix_path, "w") as temp_vsix,
    ):
        for item in source_vsix.infolist():
            content = source_vsix.read(item.filename)

            if item.filename == "extension.vsixmanifest":
                content = update_target(content, target_platform)

            temp_vsix.writestr(item, content)

    shutil.move(temp_vsix_path, vsix_file)


if __name__ == "__main__":
    args = get_args()
    for vsix_file in args.vsix_files:
        patch_vsix(vsix_file, args.target_platform)
