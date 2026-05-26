# PACA - Image Batch Processor
## Plan de Implementación en 4 Pasos

**Stack**: Python 3.9+ | Pillow | rembg  
**Objetivo**: CLI para convertir imágenes a WebP y eliminar fondo con IA local  
**Modo**: Producción (Vibe Engineering)

---

## FASE 1: Setup + Estructura Base

### 1.1 Estructura de Directorios

```
paca/
├── paca/
│   ├── __init__.py
│   ├── cli.py
│   ├── validator.py
│   ├── scanner.py
│   ├── processor.py
│   ├── reporter.py
│   └── utils.py
├── main.py
├── requirements.txt
└── .gitignore
```

### 1.2 Dependencias (requirements.txt)

```txt
Pillow>=10.0.0
rembg>=2.0.50
```

### 1.3 .gitignore

```
__pycache__/
*.py[cod]
.venv/
.DS_Store
Thumbs.db
.u2net/
```

### 1.4 __init__.py

```python
"""paca - Procesamiento por lotes de imágenes."""

__version__ = "1.0.0"

from .cli import run

__all__ = ["run"]
```

### 1.5 main.py

```python
#!/usr/bin/env python3
"""Script ejecutable para paca."""
import sys
from paca import run

if __name__ == "__main__":
    sys.exit(run())
```

### ✓ Checklist Fase 1
- [ ] Crear estructura de carpetas
- [ ] Crear requirements.txt
- [ ] Crear .gitignore
- [ ] Crear __init__.py
- [ ] Crear main.py
- [ ] Ejecutar: `python -m venv .venv`
- [ ] Ejecutar: `.venv\Scripts\activate` (Windows)
- [ ] Ejecutar: `pip install -r requirements.txt`

---

## FASE 2: Módulos Base (utils, validator, scanner)

### 2.1 utils.py

```python
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
```

### 2.2 validator.py

```python
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
```

### 2.3 scanner.py

```python
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
```

### ✓ Checklist Fase 2
- [ ] Crear utils.py
- [ ] Crear validator.py
- [ ] Crear scanner.py
- [ ] Verificar imports sin errores: `python -c "from paca import utils, validator, scanner"`

---

## FASE 3: Core (processor, reporter)

### 3.1 processor.py

```python
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
```

### 3.2 reporter.py

```python
"""Reporte de resultados del procesamiento."""
from pathlib import Path
from typing import List
from dataclasses import dataclass, field


@dataclass
class ProcessingStats:
    """Estadísticas del procesamiento."""
    
    total_processed: int = 0
    corrupted_files: List[Path] = field(default_factory=list)
    pdf_files: List[Path] = field(default_factory=list)
    system_files: List[Path] = field(default_factory=list)
    errors: List[tuple[Path, str]] = field(default_factory=list)
    
    def add_success(self) -> None:
        self.total_processed += 1
    
    def add_corrupted(self, file_path: Path) -> None:
        self.corrupted_files.append(file_path)
    
    def add_pdf(self, file_path: Path) -> None:
        self.pdf_files.append(file_path)
    
    def add_system_file(self, file_path: Path) -> None:
        self.system_files.append(file_path)
    
    def add_error(self, file_path: Path, error_msg: str) -> None:
        self.errors.append((file_path, error_msg))


def print_report(stats: ProcessingStats) -> None:
    """Imprime reporte estructurado en consola."""
    print("\n" + "="*60)
    print("REPORTE DE PROCESAMIENTO")
    print("="*60)
    
    print(f"\n✓ Imágenes procesadas exitosamente: {stats.total_processed}")
    
    if stats.corrupted_files:
        print(f"\n⚠ Archivos corruptos encontrados: {len(stats.corrupted_files)}")
        for file_path in stats.corrupted_files:
            print(f"  - {file_path}")
    
    if stats.pdf_files:
        print(f"\n⊗ Archivos PDF ignorados: {len(stats.pdf_files)}")
        for file_path in stats.pdf_files:
            print(f"  - {file_path}")
    
    if stats.system_files:
        print(f"\n⊗ Archivos de sistema ignorados: {len(stats.system_files)}")
        for file_path in stats.system_files:
            print(f"  - {file_path}")
    
    if stats.errors:
        print(f"\n✗ Errores encontrados: {len(stats.errors)}")
        for file_path, error_msg in stats.errors:
            print(f"  - {file_path}: {error_msg}")
    
    print("\n" + "="*60)
    print("FIN DEL REPORTE")
    print("="*60 + "\n")
```

### ✓ Checklist Fase 3
- [ ] Crear processor.py
- [ ] Crear reporter.py
- [ ] Verificar imports: `python -c "from paca import processor, reporter"`

---

## FASE 4: CLI + Integration + Testing

### 4.1 cli.py

```python
"""Interfaz de línea de comandos y orquestador principal."""
import argparse
import sys
from pathlib import Path

from .validator import run_preflight_checks
from .scanner import mirror_directory_structure, scan_images
from .processor import process_image
from .reporter import ProcessingStats, print_report


def parse_arguments() -> argparse.Namespace:
    """Parsea argumentos de CLI."""
    parser = argparse.ArgumentParser(
        description="paca - Procesamiento por lotes: WebP + eliminación de fondo",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--origen",
        type=Path,
        required=True,
        help="Ruta de la carpeta con las imágenes originales"
    )
    
    parser.add_argument(
        "--destino",
        type=Path,
        required=True,
        help="Ruta donde se guardarán las imágenes procesadas"
    )
    
    return parser.parse_args()


def run() -> int:
    """
    Punto de entrada principal.
    
    Flujo:
    CLI → Validación → Espejeo → Scan → Process (loop) → Report
    
    Returns:
        0 = éxito, 1 = error
    """
    args = parse_arguments()
    origin = args.origen.resolve()
    destination = args.destino.resolve()
    
    print("paca - Image Batch Processor")
    print(f"Origen: {origin}")
    print(f"Destino: {destination}")
    print()
    
    # Pre-flight checks
    print("Ejecutando validaciones...")
    success, message = run_preflight_checks(origin, destination)
    
    if not success:
        print(f"✗ Error de validación: {message}", file=sys.stderr)
        return 1
    
    print(f"✓ {message}")
    print()
    
    # Replicar estructura
    print("Replicando estructura de carpetas...")
    mirror_directory_structure(origin, destination)
    print("✓ Estructura replicada")
    print()
    
    # Inicializar estadísticas
    stats = ProcessingStats()
    
    # Procesamiento secuencial
    print("Iniciando procesamiento de imágenes...")
    print()
    
    for source_path, destination_dir in scan_images(origin, destination):
        print(f"Procesando: {source_path.name}...", end=" ")
        
        result = process_image(source_path, destination_dir)
        
        if result.success:
            stats.add_success()
            print("✓")
        else:
            if result.reason == "corrupted":
                stats.add_corrupted(source_path)
                print("⚠ Corrupto")
            elif result.reason == "pdf":
                stats.add_pdf(source_path)
                print("⊗ PDF")
            elif result.reason == "system_file":
                stats.add_system_file(source_path)
                print("⊗ Sistema")
            else:
                stats.add_error(source_path, result.reason or "Unknown error")
                print(f"✗ {result.reason}")
    
    # Reporte final
    print_report(stats)
    
    return 0
```

### 4.2 Testing Manual

```powershell
# Preparar carpetas de prueba
mkdir C:\temp\paca_test\origen
mkdir C:\temp\paca_test\destino

# Copiar algunas imágenes a origen (JPG, PNG, etc.)

# Ejecutar programa
python main.py --origen C:\temp\paca_test\origen --destino C:\temp\paca_test\destino
```

### 4.3 Verificar Salida Esperada

```
paca - Image Batch Processor
Origen: C:\temp\paca_test\origen
Destino: C:\temp\paca_test\destino

Ejecutando validaciones...
✓ Validaciones completadas exitosamente

Replicando estructura de carpetas...
✓ Estructura replicada

Iniciando procesamiento de imágenes...

Procesando: foto1.jpg... ✓
Procesando: foto2.png... ✓
Procesando: .DS_Store... ⊗ Sistema

============================================================
REPORTE DE PROCESAMIENTO
============================================================

✓ Imágenes procesadas exitosamente: 2

⊗ Archivos de sistema ignorados: 1
  - C:\temp\paca_test\origen\.DS_Store

============================================================
FIN DEL REPORTE
============================================================
```

### ✓ Checklist Fase 4
- [ ] Crear cli.py
- [ ] Verificar help: `python main.py --help`
- [ ] Crear carpetas de prueba
- [ ] Ejecutar con imágenes reales
- [ ] Verificar estructura replicada en destino
- [ ] Verificar archivos .webp generados
- [ ] Verificar reporte en consola

---

## Comandos de Ejecución

### Instalación
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Uso
```powershell
python main.py --origen C:\ruta\origen --destino C:\ruta\destino
```

### Troubleshooting

**Error: "Activate.ps1 is not digitally signed"**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Error: "No module named 'PIL'"**
```powershell
pip uninstall Pillow
pip install Pillow --no-cache-dir
```

**Primera ejecución lenta**
- rembg descarga modelo ~176 MB (solo primera vez)
- Ubicación: `C:\Users\<TuUsuario>\.u2net\u2net.onnx`

---

## Trade-offs de Diseño

| Decisión | Ventaja | Desventaja | Alternativa |
|----------|---------|------------|-------------|
| **Secuencial** | Simple, debuggeable | Lento (1-3 seg/img) | `ProcessPoolExecutor` |
| **Todo en RAM** | Rápido, sin I/O temp | Limitado por memoria | Streaming con chunks |
| **Sufijo + Contador** | Nunca sobrescribe | Nombres verbosos | Hash-based naming |

---

## Arquitectura Final

```
Flujo unidireccional:
CLI → Validación → Espejeo → Scan → Process (loop) → Report

Pipeline en memoria:
PIL.open() → BytesIO(WebP) → rembg.remove() → write_bytes()

Módulos sin dependencias circulares:
utils ← processor
validator (standalone)
scanner (standalone)
reporter ← processor
cli → todos
```

---

## Notas de Producción

- **Primera ejecución**: Requiere internet para descargar modelo U²-Net
- **Rutas con espacios**: Usar comillas en PowerShell
- **Formato de salida**: Solo WebP (con transparencia)
- **Errores**: El programa nunca se detiene por un archivo individual
- **Reporte**: Completo al final, no en tiempo real por archivo