"""Reporte de resultados del procesamiento."""
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass, field


@dataclass
class ProcessingStats:
    """Estadísticas del procesamiento."""

    total_processed: int = 0
    corrupted_files: List[Path] = field(default_factory=list)
    pdf_files: List[Path] = field(default_factory=list)
    system_files: List[Path] = field(default_factory=list)
    errors: List[Tuple[Path, str]] = field(default_factory=list)

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
    print("\n" + "=" * 60)
    print("REPORTE DE PROCESAMIENTO")
    print("=" * 60)

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

    print("\n" + "=" * 60)
    print("FIN DEL REPORTE")
    print("=" * 60 + "\n")
