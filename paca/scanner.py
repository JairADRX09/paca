"""Escaneo de directorios y replicación de estructura."""
from pathlib import Path
from typing import Iterator, Tuple


def mirror_directory_structure(origin: Path, destination: Path) -> None:
    """Replica la estructura de directorios de origen en destino."""
    destination.mkdir(parents=True, exist_ok=True)

    for origin_dir in origin.rglob("*"):
        if origin_dir.is_dir():
            relative_path = origin_dir.relative_to(origin)
            destination_dir = destination / relative_path
            destination_dir.mkdir(parents=True, exist_ok=True)


def scan_images(origin: Path, destination: Path) -> Iterator[Tuple[Path, Path]]:
    """
    Escanea recursivamente generando pares (archivo_origen, directorio_destino).
    Procesa secuencialmente: carpeta por carpeta.
    """
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

    for file_path in sorted(origin.rglob("*")):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in image_extensions:
            continue

        relative_path = file_path.parent.relative_to(origin)
        destination_dir = destination / relative_path

        yield file_path, destination_dir
