"""Pipeline de procesamiento: conversión a WebP + eliminación de fondo."""
from pathlib import Path
from typing import Optional
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from rembg import remove

from .utils import generate_safe_filename, is_system_file

# Límite de tamaño para modo web
_MAX_WEB_BYTES = 500 * 1024  # 500 KB


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


def _encode_alta(img: Image.Image) -> bytes:
    """
    WebP lossless — máxima calidad, sin límite de tamaño.
    Ideal para impresión, edición o archivado.
    """
    buf = BytesIO()
    img.save(buf, format="WEBP", lossless=True)
    return buf.getvalue()


def _encode_web(img: Image.Image) -> bytes:
    """
    WebP lossy con calidad decreciente hasta alcanzar ≤ 500 KB.
    Rango: quality 80 → 20 en pasos de 10.
    Si ningún paso lo logra, usa quality=20 como mínimo.
    """
    for quality in range(80, 10, -10):
        buf = BytesIO()
        img.save(buf, format="WEBP", quality=quality)
        if buf.tell() <= _MAX_WEB_BYTES:
            return buf.getvalue()

    # Último recurso: calidad mínima aceptable
    buf = BytesIO()
    img.save(buf, format="WEBP", quality=20)
    return buf.getvalue()


def process_image(
    source_path: Path,
    destination_dir: Path,
    calidad: str = "alta"
) -> ProcessingResult:
    """
    Pipeline: Abrir → PNG en RAM → rembg → WebP (según calidad) → Guardar

    Filtros:
    - Archivos de sistema (.DS_Store, Thumbs.db) → Skip
    - PDFs → Skip
    - Imágenes corruptas → Skip + log

    Args:
        source_path:     Ruta de la imagen original.
        destination_dir: Carpeta donde se escribe el resultado.
        calidad:         "alta" (lossless) | "web" (≤ 500 KB).
    """
    # Filtrar archivos de sistema
    if is_system_file(source_path.name):
        return ProcessingResult(success=False, reason="system_file")

    # Filtrar PDFs
    if source_path.suffix.lower() == ".pdf":
        return ProcessingResult(success=False, reason="pdf")

    try:
        with Image.open(source_path) as img:

            # Paso 2: Convertir a PNG en memoria para rembg
            # PNG preserva todos los detalles para que el modelo los procese
            png_buffer = BytesIO()
            img.save(png_buffer, format="PNG")

            # Paso 3: Eliminar fondo — rembg siempre devuelve RGBA PNG
            png_buffer.seek(0)
            png_sin_fondo = remove(png_buffer.read())

            # Paso 4: Re-codificar como WebP real según la calidad elegida
            result_img = Image.open(BytesIO(png_sin_fondo))  # siempre RGBA

            if calidad == "web":
                final_bytes = _encode_web(result_img)
            else:
                final_bytes = _encode_alta(result_img)

            # Paso 5: Guardar con nombre seguro (nunca sobreescribe)
            safe_path = generate_safe_filename(destination_dir, source_path.stem)
            safe_path.write_bytes(final_bytes)

            return ProcessingResult(success=True, output_path=safe_path)

    except UnidentifiedImageError:
        return ProcessingResult(success=False, reason="corrupted")

    except Exception as e:
        return ProcessingResult(success=False, reason=f"error: {str(e)}")
