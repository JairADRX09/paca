"""Utilidades para manejo de nombres y colisiones."""
from pathlib import Path


def generate_safe_filename(base_path: Path, stem: str, suffix: str = "_nobg") -> Path:
    """
    Genera nombre único con sufijo y contador si es necesario.
    foto.jpg -> foto_nobg.webp
    Si existe: foto_nobg_1.webp, foto_nobg_2.webp, etc.
    """
    target = base_path / f"{stem}{suffix}.webp"

    if not target.exists():
        return target

    counter = 1
    while True:
        target = base_path / f"{stem}{suffix}_{counter}.webp"
        if not target.exists():
            return target
        counter += 1


def is_system_file(filename: str) -> bool:
    """Detecta archivos de sistema que deben ser ignorados."""
    system_files = {".ds_store", "thumbs.db", "desktop.ini", ".gitkeep"}
    return filename.lower() in system_files
