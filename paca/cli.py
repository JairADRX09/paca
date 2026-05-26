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
    print(f"Origen:  {origin}")
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
        print(f"  Procesando: {source_path.name}...", end=" ", flush=True)

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
                stats.add_error(source_path, result.reason or "error desconocido")
                print(f"✗ {result.reason}")

    # Reporte final
    print_report(stats)

    return 0
