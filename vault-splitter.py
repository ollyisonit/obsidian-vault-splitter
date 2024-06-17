# Requires Python 3.12

from argparse import ArgumentParser
from pathlib import Path
import os
from typing import Dict, Optional, TypeVar
import re

parser: ArgumentParser = ArgumentParser(
    prog="Obsidian Vault Splitter",
    description=
    "Vault-splitting utility for Obsidian. Allows you to select a root note and then construct a new vault from all the notes connected to it. Only affects *.md files--any other types of file in the vault will not be tracked."
)

parser.add_argument(
    "root-note",
    help="Path to file that should be considered as root when building tree")

parser.add_argument('-c',
                    '--copy',
                    help="Copy isolated tree to given directory")
parser.add_argument('-m',
                    '--move',
                    help="Move isolated tree to given directory")
parser.add_argument('-ls',
                    '--list',
                    action='store_true',
                    help="List files without moving or copying them")
parser.add_argument('--find-orphans',
                    action='store_true',
                    help="Return all files that aren't in the tree")


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
    # for name, path in active_notes.items():
    #     print(f"{name}: {path.relative_to(vault_dir)}")
    names = [
        x.relative_to(vault_dir).as_posix() for x in active_notes.values()
    ]
    names.sort(key=lambda x: x.lower())
    for name in names:
        print(name)
