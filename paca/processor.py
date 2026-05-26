"""Pipeline de procesamiento: conversión a WebP + eliminación de fondo."""
from pathlib import Path
from typing import Optional
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from rembg import remove

from .utils import generate_safe_filename, is_system_file


class ProcessingResult:
    """Resultado del procesamiento de una imagen."""

    def __init__(
        self,
        success: bool,
        reason: Optional[str] = None,
        output_path: Optional[Path] = None
    ):
        self.success = success
        self.reason = reason
        self.output_path = output_path


def process_image(source_path: Path, destination_dir: Path) -> ProcessingResult:
    """
    Pipeline: Abrir → WebP en RAM → rembg → Guardar

    Filtros:
    - Archivos de sistema (.DS_Store, Thumbs.db) → Skip
    - PDFs → Skip
    - Imágenes corruptas → Skip + log
    """
    # Filtrar archivos de sistema
    if is_system_file(source_path.name):
        return ProcessingResult(success=False, reason="system_file")

    # Filtrar PDFs
    if source_path.suffix.lower() == ".pdf":
        return ProcessingResult(success=False, reason="pdf")

    try:
        # Paso 1: Abrir imagen
        with Image.open(source_path) as img:

            # Paso 2: Convertir a WebP en memoria
            webp_buffer = BytesIO()

            if img.mode in ("RGBA", "LA", "P"):
                img.save(webp_buffer, format="WEBP", lossless=True)
            else:
                rgb_img = img.convert("RGB")
                rgb_img.save(webp_buffer, format="WEBP", quality=95)

            # Paso 3: Eliminar fondo con rembg
            webp_buffer.seek(0)
            image_with_bg = webp_buffer.read()
            image_without_bg = remove(image_with_bg)

            # Paso 4: Guardar
            safe_path = generate_safe_filename(destination_dir, source_path.stem)
            safe_path.write_bytes(image_without_bg)

            return ProcessingResult(success=True, output_path=safe_path)

    except UnidentifiedImageError:
        return ProcessingResult(success=False, reason="corrupted")

    except Exception as e:
        return ProcessingResult(success=False, reason=f"error: {str(e)}")
