"""Validaciones pre-vuelo antes de iniciar el procesamiento."""
import shutil
from pathlib import Path
from typing import Tuple


class ValidationError(Exception):
    """Excepción para errores de validación críticos."""
    pass


def validate_origin(origin_path: Path) -> None:
    """Valida que la ruta de origen exista y sea un directorio."""
    if not origin_path.exists():
        raise ValidationError(f"La ruta de origen no existe: {origin_path}")

    if not origin_path.is_dir():
        raise ValidationError(f"La ruta de origen no es un directorio: {origin_path}")


def validate_disk_space(destination_path: Path, min_space_mb: int = 500) -> None:
    """Valida que la unidad de destino tenga espacio suficiente."""
    stat = shutil.disk_usage(destination_path.parent if destination_path.exists() else destination_path.anchor)
    free_mb = stat.free / (1024 * 1024)

    if free_mb < min_space_mb:
        raise ValidationError(
            f"Espacio insuficiente. Disponible: {free_mb:.1f} MB, Requerido: {min_space_mb} MB"
        )


def run_preflight_checks(origin: Path, destination: Path) -> Tuple[bool, str]:
    """Ejecuta todas las validaciones pre-vuelo."""
    try:
        validate_origin(origin)
        validate_disk_space(destination)
        return True, "Validaciones completadas exitosamente"
    except ValidationError as e:
        return False, str(e)
