# Requires Python 3.12

from argparse import ArgumentParser
from pathlib import Path
import os
from typing import Dict, Optional, TypeVar
import re
import shutil

parser: ArgumentParser = ArgumentParser(
    description=
    "Vault-splitting utility for Obsidian. Allows you to select a root note and then recursively list, move, or copy all notes that it links to. Does not follow backlinks."
)

parser.add_argument(
    "root-note",
    help="Path to file that should be considered as root when building tree")

parser.add_argument('-cp',
                    '--copy',
                    metavar='PATH',
                    help="Copy isolated tree to given directory")
parser.add_argument('-mv',
                    '--move',
                    metavar='PATH',
                    help="Move isolated tree to given directory")
parser.add_argument(
    '-ls',
    '--list',
    action='store_true',
    help="List files without moving or copying them. Default behavior.")
parser.add_argument(
    '--find-orphans',
    action='store_true',
    help="Invert behavior to affect all files that aren't in the tree")


def resolve_path(path: Optional[Path]) -> Optional[Path]:
    """Leaves path as-is if it's absolute, and makes it relative to the working directory if it isn't"""
    if path is None:
        return None

    if not os.path.isabs(path):
        path = Path(os.getcwd()).joinpath(path)
    else:
        path = Path(path)
    if not path.exists():
        raise ValueError(f"Path not found: {path.as_posix()}")
    return path


T = TypeVar('T')


def unpack_optional(opt: Optional[T]) -> T:
    if opt is None:
        raise ValueError("Optional value is None")
    return opt


args = vars(parser.parse_args())
root_note = unpack_optional(resolve_path(args["root-note"]))
copy_dir = resolve_path(args["copy"])
move_dir = resolve_path(args["move"])
list_mode: bool = args["list"]
orphan_mode: bool = args["find_orphans"]

if root_note.suffix != ".md":
    raise ValueError("Root note is not an .md file!")

selected_modes = 0
if copy_dir:
    selected_modes += 1
if move_dir:
    selected_modes += 1
if list_mode:
    selected_modes += 1
if selected_modes > 1:
    raise ValueError("Can only select one of --copy, --move, --list")
if selected_modes == 0:
    list_mode = True

vault_dir = root_note.parent

while True:
    if not vault_dir.joinpath(".obsidian").exists():
        if vault_dir == Path(vault_dir.anchor):
            raise ValueError("Given root note is not part of vault!")
        vault_dir = vault_dir.parent
        if vault_dir is None:
            raise ValueError("Given root note is not part of vault!")
    else:
        break

unprocessed_notes: Dict[str, Path] = {}
in_tree: Dict[str, Path] = {}
for note in vault_dir.glob("**/*"):
    if note.is_relative_to(
            vault_dir.joinpath(".obsidian")) or note.is_relative_to(
                vault_dir.joinpath(".trash")):
        continue
    if note.suffix == ".md":
        unprocessed_notes[note.stem] = note
    else:
        unprocessed_notes[note.name] = note


def add_to_tree(note_name: str):
    if note_name in unprocessed_notes.keys():
        name = note_name
        path = unprocessed_notes[name]
        in_tree[name] = path
        unprocessed_notes.pop(name)

        if path.suffix == ".md":
            with open(path, "r") as note_file:
                matches = re.findall(r"[^\\]?\[\[(.*?[^\\]?)\]\]",
                                     note_file.read())
                for match in matches:
                    add_to_tree(match)


add_to_tree(root_note.stem)

active_notes: Dict[str, Path] = {}
if not orphan_mode:
    active_notes = in_tree
else:
    active_notes = unprocessed_notes

if list_mode:
    names = [
        x.relative_to(vault_dir).as_posix() for x in active_notes.values()
    ]
    names.sort(key=lambda x: x.lower())
    for name in names:
        print(name)
    if len(names) == 0:
        print("No notes match the given criteria.")
elif copy_dir or move_dir:
    target_path = Path()
    if copy_dir:
        target_path = copy_dir
    elif move_dir:
        target_path = move_dir

    for file in active_notes.values():
        print(f"{file} -> {target_path}")
        new_path = target_path.joinpath(file.relative_to(vault_dir))
        os.makedirs(new_path.parent, exist_ok=True)
        if copy_dir:
            shutil.copy2(file, new_path)
        elif move_dir:
            shutil.move(file, new_path)
