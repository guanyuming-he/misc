#!/usr/bin/env python3
# This file is licensed under the GNU GPL v3.
# Copyright (C) 2026 Guanyuming He.


import os
import sys
import subprocess
from pathlib import Path

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

# An empty line to mark the end
NOTICE = """This file is licensed under the GNU GPL v3.
Copyright (C) 2026 Guanyuming He.
"""
# Don't use split line on NOTICE to produce this.
# Instead, just hard code to ensure the first line never changes.
NOTICE_MARKER = "This file is licensed under the GNU GPL v3"

# Directories to scan, relative to the Git root
FILE_DIRS = ["src", "scripts"]

# File extensions
C_EXTS = {".c", ".cpp", ".h", ".hpp"}
SCRIPT_EXTS = {".sh", ".bash", ".py"}
TEX_EXTS = {".tex"}


# ----------------------------------------------------------------------
# Helpers
# You may notice that none of the file processing helpers check if the path
# exists. This is because main() ensures that before calling anything.
# ----------------------------------------------------------------------
def is_git_work_tree() -> bool:
	"""@returns True iff cwd is inside a git work tree."""
	try:
		result = subprocess.run(
			["git", "rev-parse", "--is-inside-work-tree"],
			capture_output=True,
			text=True,
			check=True,
		)
		return result.stdout.strip() == "true"
	except subprocess.CalledProcessError:
		return False


def git_root() -> Path:
	"""@returns the absolute path of the Git root directory."""
	try:
		result = subprocess.run(
			["git", "rev-parse", "--show-toplevel"],
			capture_output=True,
			text=True,
			check=True,
		)
		return Path(result.stdout.strip())
	except subprocess.CalledProcessError:
		print("git_root: Forgot to check is_git_work_tree?", file=sys.stderr)
		sys.exit(1)


def git_work_tree_clean() -> bool:
	"""@returns True iff git work tree is clean"""
	try:
		result = subprocess.run(
			["git", "status", "--porcelain"],
			capture_output=True,
			text=True,
			check=True,
		)
		if result.stdout.strip(): # Non-empty; not clean
			return False
	except subprocess.CalledProcessError:
		return False

	return True


def has_file_notice(file_path: Path, end:int = 5) -> int:
	"""
	Check if the file already has the license notice.
	@param end till which the notice is checked
	@returns the ln of the first line of the first notice found, or -1.
	"""
	with file_path.open('r') as f:
		for ln in range(end):
			line = f.readline()
			if "This file is licensed under the GNU GPL v3" in line:
				return ln
	return -1


def insert_notice(file_path: Path, prefix: str = "", insert_line: int = 0):
	"""
	Insert the license notice into the file at the given line.
	@param prefix which is to be prepended to each line of notice
	@param insert_line before which the notice is to be inserted (0 based).
	"""
	with file_path.open('r') as f:
		lines = f.readlines()

	notice_lines = [f"{prefix}{line}\n" for line in NOTICE.splitlines()]
	insert_index = max(0, min(insert_line, len(lines)))
	lines = (
		lines[:insert_index] + notice_lines + 
		['\n'] + # An empty line to mark the end
		lines[insert_index:]
	)

	with file_path.open("w", encoding="utf-8") as f:
		f.writelines(lines)


def remove_existing_notice(path: Path, start:int = 0):
	"""
	Removes the first occurrance of the NOTICE,
	up till the first empty line.
	"""
	with path.open("r+") as f:
		lines = f.readlines()

		out = lines[:start]
		# 0: actively scan
		# 1: found notice, skipping
		# 2: don't scan
		# If in the future I want to remove all,
		# then just remove 2 from out values.

		skipping = 0

		for i in range(start, len(lines)):
			if skipping == 0:
				if NOTICE_MARKER in lines[i]:
					skipping = 1
				else:
					out.append(lines[i])
			elif skipping == 1:
				# stop skipping after first empty line
				if lines[i].strip() == "":
					skipping = 2
			else:
				out.append(lines[i])

		# rewrite file in place
		f.seek(0)
		f.truncate()
		f.writelines(out)


def decide_notice(file_path: Path):
	"""Decide how to insert the notice based on file type and content."""
	old:int = has_file_notice(file_path)
	if old != -1:
		# If existing, then update by removing and then inserting.
		remove_existing_notice(file_path, old)

	print(f"Adding notice for {file_path}")

	# init as None to catch cases when they are not assigned
	prefix:str = None
	insert_line: int = None

	suffix = file_path.suffix.lower()
	if suffix in C_EXTS:
		prefix = "// "; insert_line = 0
	elif suffix in SCRIPT_EXTS:
		prefix = "# "
		with file_path.open("r", encoding="utf-8") as f:
			first_line = f.readline()
		# Check for shebang
		if first_line.startswith("#!"):
			insert_line = 1
		else:
			insert_line = 0
	elif suffix in TEX_EXTS:
		prefix = "% "; insert_line = 0
	else:
		prefix = "// "; insert_line = 0

	insert_notice(file_path, prefix, insert_line)

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def usage(prog_name: str):
	"""
	@param prog_name: pass sys.argv[0]
	"""
	print("Usage:")
	print(f"{prog_name} --help: Show this help message")
	print(f"{prog_name} paths ...: Run this script on all paths, recursively.")


def main():
	args = sys.argv[1:]
	if "--help" in args or len(args) == 0:
		usage(sys.argv[0])
		return 0

	if not is_git_work_tree():
		print("Not called within a Git work tree.", file=sys.stderr)
		return -1

	root = git_root()

	if not git_work_tree_clean():
		print("""WARNING:
Git work tree not clean (changes not tracked); possible data
loss if you run this script!
		ABORT!!!
		""")
		return -1

	for p in args:
		path = Path(p)
		if not path.is_absolute():
			path = root / path
		if path.is_file():
			decide_notice(path)
		elif path.is_dir():
			for file_path in path.rglob("*"):
				if  not file_path.is_file() or \
					not os.access(file_path, os.W_OK | os.R_OK):
					continue
				decide_notice(file_path)

	return 0


if __name__ == "__main__":
	sys.exit(main())

