# Obsidian Vault Splitter

A small command line utility for splitting up your Obsidian vaults. Allows you to select one note as the root, and then recursively grabs all of the notes it references.

Requires Python 3.10 or later.

**CAUTION**: Make sure to back up your vault before splitting it.

```
usage: vault-splitter.py [-h] [-cp PATH] [-mv PATH] [-ls] [--find-orphans] root-note

Vault-splitting utility for Obsidian. Allows you to select a root note and then recursively list, move, or copy all notes that it links to. Does not follow backlinks.

positional arguments:
  root-note             Path to file that should be considered as root when building tree

options:
  -h, --help            show this help message and exit
  -cp PATH, --copy PATH
                        Copy isolated tree to given directory
  -mv PATH, --move PATH
                        Move isolated tree to given directory
  -ls, --list           List files without moving or copying them. Default behavior.
  --find-orphans        Invert behavior to affect all files that aren't in the tree
```
