# PACA — Image Batch Processor

CLI en Python que procesa imágenes por lotes: las convierte a **WebP** y les elimina el fondo automáticamente con IA local (rembg / U²-Net). Sin conexión a servicios externos, todo corre en tu máquina.

---

## ¿Qué hace?

- Escanea recursivamente una carpeta de origen
- Elimina el fondo de cada imagen con inteligencia artificial
- Convierte el resultado a **WebP con canal alfa** (fondo transparente)
- Replica la estructura de subcarpetas en el destino
- Nunca sobreescribe archivos existentes
- Un archivo corrupto no detiene el proceso — se reporta al final

---

## Requisitos

- Python **3.9** o superior
- Windows / macOS / Linux
- ~200 MB de espacio para el modelo U²-Net (se descarga automáticamente la primera vez)

---

## Instalación

### 1. Clonar el repositorio

```powershell
git clone https://github.com/JairADRX09/paca.git
cd paca
```

### 2. Crear el entorno virtual

```powershell
python -m venv .venv
```

### 3. Activar el entorno virtual

**Windows:**
```powershell
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

> Si en Windows aparece el error `Activate.ps1 is not digitally signed`, ejecuta primero:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 4. Instalar dependencias

```powershell
pip install -r requirements.txt
```

---

## Uso

```powershell
python main.py --origen <ruta_origen> --destino <ruta_destino> [--calidad {alta,web}]
```

### Argumentos

| Argumento | Requerido | Descripción |
|---|---|---|
| `--origen` | ✅ Sí | Carpeta con las imágenes originales |
| `--destino` | ✅ Sí | Carpeta donde se guardarán los resultados |
| `--calidad` | ❌ No | `alta` (default) o `web`. Ver detalle abajo |

---

## Modos de calidad

### `--calidad alta` *(default)*
WebP **lossless** — sin pérdida de calidad, sin límite de tamaño.
Ideal para archivado, impresión o seguir editando las imágenes.

```powershell
python main.py --origen C:\Fotos\productos --destino C:\Fotos\procesadas
```
```powershell
python main.py --origen C:\Fotos\productos --destino C:\Fotos\procesadas --calidad alta
```

---

### `--calidad web`
WebP **lossy** optimizado — máximo **500 KB** por imagen.
Ideal para tiendas online, portfolios o cualquier sitio donde la velocidad de carga importa.

```powershell
python main.py --origen C:\Fotos\productos --destino C:\Fotos\web --calidad web
```

El programa ajusta la calidad automáticamente (de 80 hacia abajo) hasta que el archivo entre en los 500 KB.

---

## Ejemplos

**Ruta simple:**
```powershell
python main.py --origen C:\Fotos\originales --destino C:\Fotos\sin-fondo --calidad web
```

**Ruta con espacios (usar comillas):**
```powershell
python main.py --origen "C:\Mis Fotos\producto shot" --destino "C:\Mis Fotos\sin fondo" --calidad alta
```

**Ver ayuda:**
```powershell
python main.py --help
```

---

## Salida en consola

```
paca - Image Batch Processor
Origen:  C:\Fotos\productos
Destino: C:\Fotos\sin-fondo
Calidad: WEB  (máx. 500 KB por imagen)

Ejecutando validaciones...
✓ Validaciones completadas exitosamente

Replicando estructura de carpetas...
✓ Estructura replicada

Iniciando procesamiento de imágenes...

  Procesando: camisa-azul.jpg...  ✓  (187 KB)
  Procesando: zapato-negro.png... ✓  (243 KB)
  Procesando: bolso.jpg...        ✓  (312 KB)

============================================================
REPORTE DE PROCESAMIENTO
============================================================

✓ Imágenes procesadas exitosamente: 3

============================================================
FIN DEL REPORTE
============================================================
```

---

## Formatos de entrada soportados

| Formato | Extensión |
|---|---|
| JPEG | `.jpg`, `.jpeg` |
| PNG | `.png` |
| WebP | `.webp` |
| GIF | `.gif` |
| BMP | `.bmp` |
| TIFF | `.tiff` |

El formato de salida es siempre **WebP con transparencia** (canal alfa).

---

## Estructura del proyecto

```
paca/
├── paca/
│   ├── __init__.py       # Punto de entrada del paquete
│   ├── cli.py            # Orquestador y argumentos CLI
│   ├── processor.py      # Pipeline: PNG → rembg → WebP
│   ├── reporter.py       # Reporte final de resultados
│   ├── scanner.py        # Escaneo recursivo y espejeo de carpetas
│   ├── validator.py      # Validaciones pre-vuelo
│   └── utils.py          # Nombres seguros, filtros de sistema
├── main.py               # Script ejecutable
├── requirements.txt      # Dependencias
└── .gitignore
```

---

## Notas

- **Primera ejecución:** rembg descarga el modelo U²-Net (~176 MB) automáticamente. Solo ocurre una vez. Requiere conexión a internet en ese momento.
- **Modelo guardado en:** `C:\Users\<TuUsuario>\.u2net\u2net.onnx`
- **Nombres de salida:** `foto.jpg` → `foto_nobg.webp`. Si ya existe, genera `foto_nobg_1.webp`, `foto_nobg_2.webp`, etc.
- **Velocidad:** ~1–3 segundos por imagen dependiendo del tamaño y la CPU.
