"""Language backends: turn source files into FunctionInfo without running them.

One module per language, each exposing the same two functions:

    discover(path) -> list[Path]           which files to look at
    extract(file)  -> list[FunctionInfo]   what functions are in one file

python.py is v1. gdscript.py (Godot) is v2 and must fit behind the same
two signatures, so keep anything Python-specific inside python.py.
"""
