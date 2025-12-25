import pathlib


def show_py_contents(path=".", allowed_extensions=None):
    """
    Walks through the directory tree. If it finds a file with an allowed extension,
    it prints the filename followed by its contents.

    allowed_extensions: List of strings, e.g., ['.py', '.txt', '.md']
    """
    if allowed_extensions is None:
        allowed_extensions = ['.py', '.csv','.toml']

    root = pathlib.Path(path)

    if not root.exists():
        print(f"Error: The path '{path}' does not exist.")
        return

    print(f"🔍 Scanning for files {allowed_extensions} in: {root.resolve()}\n")
    _process_directory(root, allowed_extensions)


def _process_directory(directory, allowed_extensions):
    # Sort items for consistent order
    try:
        items = sorted(directory.iterdir(), key=lambda x: x.name.lower())
    except PermissionError:
        print(f"⚠️  Permission denied: {directory}")
        return

    for item in items:
        # 1. Filter out hidden files/folders and __pycache__
        if item.name.startswith('.') or item.name == "__pycache__":
            continue

        # 2. If it's a directory, recurse into it
        if item.is_dir():
            _process_directory(item, allowed_extensions)

        # 3. If it's a file and extension matches, show contents
        elif item.is_file() and item.suffix in allowed_extensions:
            _print_file_content(item)


def _print_file_content(file_path):
    print("\n" + "=" * 60)
    print(f"📄 FILE: {file_path}")
    print("=" * 60 + "\n")

    try:
        # Read and print the content
        content = file_path.read_text(encoding='utf-8')
        print(content)
        print("\n" + "-" * 60)  # End of file marker
    except Exception as e:
        print(f"❌ Could not read file: {e}")


if __name__ == "__main__":
    # Add extensions here: e.g., ['.py', '.txt', '.md', '.json']
    show_py_contents(".", allowed_extensions=['.py', '.txt', '.md', '.csv','.toml'])