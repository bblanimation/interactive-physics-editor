#!/usr/bin/env python
# Author: Christopher Gearhart

# System imports
import os
from os.path import join, split, exists, dirname, realpath, isfile, isdir
import shutil
import argparse
import zipfile

# TO RUN: python zip_addon --beta
# NOTE: only send the resulting zip file to verified customers


# initialize arguments
parser = argparse.ArgumentParser(description="Zip addon")
parser.add_argument(
    "--alpha",
    help="Bundle as alpha version",
    dest="alpha",
    action="store_true",
)
parser.add_argument(
    "--beta",
    help="Bundle as beta version",
    dest="beta",
    action="store_true",
)
args = parser.parse_args()


# helper functions
def copy_directory(src, dest):
    try:
        shutil.copytree(src, dest)
    # Directories are the same
    except shutil.Error as e:
        print(f"Directory not copied. Error: {e}")
    # Any error saying that the directory doesn"t exist
    except OSError as e:
        print(f"Directory not copied. Error: {e}")


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


def edit_bl_info_warning_message(filepath, warning_msg=""):
    # read lines
    with open(filepath, "r") as f:
        data = f.readlines()

    # make adjustments
    for i, line in enumerate(data):
        if "\"warning\"" in line:
            start_idx = line.find(": \"")
            end_idx = line.find("\",")
            data[i] = line.replace(line[start_idx + 2:end_idx + 2], f"\"{warning_msg}\",")
            break

    # write lines
    with open(filepath, "w") as f:
        f.writelines(data)


def parse_file_for_bl_info_version(filepath):
    version = ""
    line = None
    with open(filepath, "r") as f:
        while line != "":
            line = f.readline()
            if "\"version\"" in line:
                start_idx = line.find(": (")
                end_idx = line.find(")")
                version = line[start_idx + 3:end_idx]
                break
    return version


def get_addon_directory():
    return dirname(realpath(__file__))


def parse_git_files_for_branch():
    head_dir = join(get_addon_directory(), ".git", "HEAD")
    with open(head_dir, "r") as f:
        content = f.read().splitlines()

    for line in content:
        if line[0:4] == "ref:":
            return line.partition("refs/heads/")[2]



# main functionality
def main():
    current_dir_path = get_addon_directory()
    parent_dir_path, current_dir_name = split(current_dir_path)
    addon_version = parse_file_for_bl_info_version(join(current_dir_path, "__init__.py"))
    branch_name = parse_git_files_for_branch()
    demo_version = branch_name == "demo"
    new_dir_name = current_dir_name
    assert addon_version != "" and isinstance(addon_version, str)
    new_dir_name += "_v" + addon_version.replace(", ", "-")
    if demo_version:
        new_dir_name += "_demo"
    elif args.alpha:
        new_dir_name += "_alpha"
    elif args.beta:
        new_dir_name += "_beta"
    # clear out old destination directories
    new_dir_path = join(parent_dir_path, new_dir_name)
    if exists(new_dir_path):
        shutil.rmtree(new_dir_path)
    if exists(f"{new_dir_path}.zip"):
        os.remove(f"{new_dir_path}.zip")
    # make the destination directory
    copy_directory(current_dir_path, new_dir_path)
    try:
        # make sure the directory contents copied successfully (just checks for the init file)
        new_init_filepath = join(new_dir_path, "__init__.py")
        assert exists(new_init_filepath)
        # adjust bl_info for beta
        if demo_version:
            edit_bl_info_warning_message(new_init_filepath, "Demo Version - Full version available at the Blender Market!")
        elif args.alpha:
            edit_bl_info_warning_message(new_init_filepath, "Unstable Alpha release - update to official release when available")
        elif args.beta:
            edit_bl_info_warning_message(new_init_filepath, "Unstable Beta release - update to official release when available")
        else:
            edit_bl_info_warning_message(new_init_filepath, "")
        # remove unnecessary files/directories
        for filename in ("developer-notes.md", "zip_addon.py", "error_log", ".git", ".gitignore", ".github", "__pycache__", f"{current_dir_name}_updater"):
            filepath = join(new_dir_path, filename)
            if not exists(filepath):
                continue
            elif isfile(filepath):
                os.remove(filepath)
            elif isdir(filepath):
                shutil.rmtree(filepath)
        # zip new directory
        shutil.make_archive(new_dir_path, "zip", parent_dir_path, new_dir_name)
        print(f"Created new archive: '{split(new_dir_path)[-1]}'")
    finally:
        # remove new directory
        shutil.rmtree(new_dir_path)


main()
