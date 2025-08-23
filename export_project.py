from pathlib import Path
import shutil

#python code to create a folder with everything required to run the project

def copy_items_to_folder(sources, dest_folder, ignore_names=["__pycache__"]):
    dest_folder = Path(dest_folder)
    dest_folder.mkdir(parents=True, exist_ok=True)

    for src in sources:
        src_path = Path(src)
        name = src_path.name
        if name in ignore_names:
            continue

        dest_path = dest_folder / name

        if src_path.is_file():
            shutil.copy2(src_path, dest_path)
        elif src_path.is_dir():
            if dest_path.exists():
                for item in src_path.iterdir():
                    copy_items_to_folder([item], dest_path, ignore_names)
            else:
                # Crée une copie récursive, mais sans les dossiers à ignorer
                def ignore_func(_, names):
                    return [n for n in names if n in ignore_names]

                shutil.copytree(src_path, dest_path, ignore=ignore_func)
        else:
            print(f"⚠️ Chemin ignoré (ni fichier ni dossier) : {src_path}")

files = [
    "export_project.py",
    "main.py",
    "presenter.py",
    "__init__.py",
    "data.toml",
    "tamasfe.even-better-toml-0.21.2.vsix",
    "theFunc.py",
    "version_python.png",
    "README.md"
]
folders = [
    "model",
    "py_libs",
    "view"
]
sources = files + folders

destination = "to_export"

copy_items_to_folder(sources, destination)
