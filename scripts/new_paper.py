#!/usr/bin/env python3
"""
new_paper.py — scaffold a new APA 7 paper project.

Usage:
    python3 ~/.claude/scripts/new_paper.py "Paper Title" /path/to/project

Creates:
    /path/to/project/
    ├── Manuscript/
    │   ├── main.tex          (APA 7 template, pre-configured)
    │   └── tables/           (generated tables land here)
    ├── Figures/              (generated figures land here)
    ├── Analysis/
    │   ├── paper_utils.py    (results writer and figure helpers)
    │   └── analysis.ipynb    (template notebook)
    └── Makefile              (make / make notebooks / make manuscript)
"""

import argparse
import os
import shutil
import sys
import re


TEMPLATE_DIR = os.path.expanduser("~/Documents/_LocalCoding/writing/paper_template")


def slugify(title):
    """Convert a title to a safe directory/command name."""
    s = re.sub(r"[^a-zA-Z0-9\s]", "", title)
    return "_".join(s.split())


def patch_tex(path, title, short_title):
    with open(path) as f:
        content = f.read()
    content = content.replace("Paper Title", title)
    content = content.replace("SHORT TITLE", short_title)
    content = content.replace("Short Title", short_title.title())
    with open(path, "w") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description="Scaffold a new APA 7 paper project")
    parser.add_argument("title", help="Paper title (quoted)")
    parser.add_argument("dest",  help="Destination directory (will be created)")
    args = parser.parse_args()

    title       = args.title
    dest        = os.path.abspath(args.dest)
    short_title = slugify(title)[:30].upper()

    if os.path.exists(dest):
        print(f"Error: {dest} already exists. Choose a new path.")
        sys.exit(1)

    if not os.path.isdir(TEMPLATE_DIR):
        print(f"Error: template directory not found at {TEMPLATE_DIR}")
        sys.exit(1)

    print(f"Creating project: {dest}")
    shutil.copytree(TEMPLATE_DIR, dest)

    # Patch the title into main.tex
    tex_path = os.path.join(dest, "Manuscript", "main.tex")
    patch_tex(tex_path, title, short_title)

    print()
    print("  Project structure:")
    for dirpath, dirnames, filenames in os.walk(dest):
        # Skip hidden and LaTeX aux files
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        level = dirpath.replace(dest, "").count(os.sep)
        indent = "  " + "  " * level
        folder = os.path.basename(dirpath)
        print(f"{indent}{folder}/")
        subindent = "  " + "  " * (level + 1)
        for f in filenames:
            print(f"{subindent}{f}")

    print()
    print("  Next steps:")
    print(f"    cd {dest}")
    print( "    make notebooks   # execute analysis and write results.tex")
    print( "    make manuscript  # compile PDF")
    print( "    make             # both")
    print()
    print("  In your notebook:  from paper_utils import Results, save_figure, save_table")
    print("  In your .tex:      \\NParticipants, \\Age, \\MalePercent, ...")


if __name__ == "__main__":
    main()
