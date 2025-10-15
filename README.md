# ⚡ Sonel Analysis Data Extractor

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://www.postgresql.org)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ChrisitanLP/SonelAnalysis)

Sonel Data Extractor es un sistema automatizado ETL (Extract, Transform, Load) para procesar datos de mediciones eléctricas desde archivos PQM de medidores de calidad de energía Sonel Analysis, transformarlos y cargarlos en una base de datos PostgreSQL.

---

## 📋 Tabla de Contenidos

- [Características principales](#-características-principales)
- [Requisitos del Sistema](#-requisitos-del-sistema)
- [Instalación](#-instalación)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Empaquetado como Ejecutable](#-empaquetado-como-ejecutable)
- [Validación y formato de datos](#-validación-y-formato-de-datos)
- [Parámetros Eléctricos Procesados](#-parámetros-eléctricos-procesados)
- [Solución de problemas](#-solución-de-problemas)
- [Logs y Diagnóstico](#-logs-y-diagnóstico)
- [Estructura de Base de Datos](#-estructura-de-base-de-datos)
- [Contribución](#-contribución)

---

## 📌 Características principales

- ✅ **Extracción Automatizada:** Automatización de la interfaz gráfica de Sonel Analysis para exportar datos  
- ✅ **Transformación Inteligente:** Detección automática de formatos CSV y estandarización de datos  
- ✅ **Carga a PostgreSQL:** Inserción en tablas normalizadas y desnormalizadas  
- ✅ **Interfaz Gráfica:** Panel de control intuitivo con monitoreo en tiempo real  
- ✅ **Gestión de Estado:** Seguimiento de archivos procesados para evitar duplicados  
- ✅ **Sistema de Recuperación:** Respaldo automático con extracción basada en coordenadas  
- ✅ **Logging Completo:** Registro detallado de todas las operaciones 

---

## 🧩 Requisitos del Sistema

### 🖥️ Software Requerido
- **Sistema Operativo:** Windows 10/11 (64-bit)
- **Python:** 3.8 o superior
- **Sonel Analysis:** Versión 4.6.6
- **PostgreSQL:** Versión 12 o superior

### ⚙️ Hardware Mínimo
- **CPU:** Dual-core 2.0 GHz  
- **RAM:** 4 GB  
- **Almacenamiento:** 2 GB libres  

---

## 📦 Instalación

### 1. Clonar o descargar el proyecto
```bash
git clone https://github.com/ChrisitanLP/SonelAnalysis
cd sonel-data-extractor
```

### 2. Crear entorno virtual
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=db_name
DB_USER=db_user
DB_PASSWORD=db_your_password
```

### 5. Crear base de datos
```bash
# Conectar a PostgreSQL
psql -U db_user

# Crear base de datos
CREATE DATABASE db_name;
```
> El sistema creará las tablas automáticamente en el primer uso.

---

## 📁 Estructura del proyecto

```
sonel:.
├───config/
│   └───__pycache__/
├───data/
│   ├───archivos_csv/
│   └───archivos_pqm/
├───database/
│   └───__pycache__/
├───etl/
│   └───__pycache__/
├───extractors/
│   ├───extras/
│   ├───pyautogui_extractor/
│   │   └───__pycache__/
│   ├───pywinauto_extractor/
│   │   └───__pycache__/
│   └───__pycache__/
├───logs/
│   └───components/
├───parser/
│   └───__pycache__/
├───temp/
├───transformers/
│   └───__pycache__/
└───utils/
    └───__pycache__/
```

## 📁 Estructura de Directorios en modo Portable
```
sonel/
├── data/
│   ├── archivos_pqm/    # Colocar archivos .pqm aquí
│   └── archivos_csv/    # Archivos CSV generados
├── logs/                # Archivos de log
└── temp/                # Archivos temporales
```

### 📂 Descripción detallada de módulos

| 📁 Carpeta                 | Descripción                                                                                                                                       |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| 🔧 `config/`              | Contiene archivos de configuración del sistema y parámetros globales utilizados en distintas fases del ETL.                                      |
| 📊 `data/`                | Directorio central para los datos de entrada, organizado en subdirectorios:                                                                      |
|                           | ├── `archivos_csv/`: Almacena archivos CSV exportados manual o automáticamente.                                                                  |
|                           | └── `archivos_pqm/`: Contiene archivos `.pqm702` generados por Sonel Analysis.                                                                   |
| 🗄️ `database/`            | Módulo encargado de la conexión con la base de datos PostgreSQL y la ejecución de operaciones SQL.                                                |
| 🔄 `etl/`                 | Lógica de orquestación del proceso de Extracción, Transformación y Carga (ETL).                                                                  |
| 🔌 `extractors/`          | Agrupa métodos de extracción de datos:                                                                                                            |
|                           | ├── `pyautogui_extractor/`: Automatización con PyAutoGUI.                                                                                         |
|                           | ├── `pywinauto_extractor/`: Automatización estructurada con Pywinauto.                                                                           |
|                           | └── `extras/`: Funciones auxiliares para extracción no convencional.                                                                              |
| 📝 `logs/`                | Sistema de logging del proceso y depuración.                                                                                                     |
|                           | └── `components/`: Submódulos de logging especializados.                                                                                          |
| 🔍 `parser/`              | Analiza el contenido bruto de los archivos y lo estructura para su transformación.                                                               |
| ⏳ `temp/`                | Directorio temporal para archivos intermedios generados durante la ejecución.                                                                    |
| 🔄 `transformers/`        | Funciones de transformación: limpieza, normalización y adaptación al esquema destino.                                                            |
| 🛠️ `utils/`              | Funciones de utilidad reutilizables en distintas partes del sistema.                                                                             |

> ⚠️ **Importante:** Las carpetas `__pycache__/` son generadas automáticamente por Python para almacenar bytecode compilado y **no deben modificarse manualmente**.

### 🏗️ Principios de arquitectura

Esta estructura sigue los principios de:

- **📦 Separación de responsabilidades**: Cada módulo tiene una función específica
- **🔄 Reutilización de código**: Componentes modulares y utilities compartidas
- **🛡️ Mantenibilidad**: Organización clara que facilita actualizaciones y debugging
- **📈 Escalabilidad**: Estructura que permite agregar nuevos extractors y transformers fácilmente

---

## ⚙️ Configuración

### Archivo `config.ini`

```ini
[DATABASE]
host = localhost
port = 5432
database = db_name
user = db_user
password = db_your_password

[PATHS]
input_dir = ./data/archivos_pqm
output_dir = ./data/archivos_csv
temp_dir = ./temp

[LOGGING]
level = INFO
file = logs/sonel_app.log
```

### Archivo `.env` 

```env
DB_HOST=localhost
DB_PORT=----
DB_NAME=sonel
DB_USER=postgres
DB_PASSWORD=*******
DATA_DIR=./data
EXPORT_DIR=./exports
```

---

## 🚀 Uso

### Ejecución Básica
```bash
# Activar entorno virtual
venv\Scripts\activate

# Ejecutar aplicación
python app.py
```

### Interfaz Gráfica

* **📁 Seleccionar Carpeta:** Escoge el directorio con archivos PQM
* **▶️ Procesar Archivos:** Inicia el procesamiento
* **📊 Monitorear Progreso:** Visualiza el estado una vez finalizado el proceso
* **📈 Revisar Resultados:** Revisa las pestañas General, CSV y Base de Datos

---
## 🧱 Empaquetado como Ejecutable

### Generar Versión Portable

```bash
python build_executable.py
```

Este proceso:

1. Verifica dependencias
2. Limpia compilaciones anteriores
3. Genera `.spec` para PyInstaller
4. Compila el ejecutable
5. Crea carpeta portable `SonelDataExtractor_Portable/`

### Distribución del Ejecutable

```
SonelDataExtractor_Portable/
├── SonelDataExtractor.exe
├── qt.conf
├── config.ini
├── README.txt
├── TROUBLESHOOTING.txt
├── data/
│   ├── archivos_pqm/
│   └── archivos_csv/
├── logs/
└── temp/
```

**Uso del Ejecutable:**

1. Copiar toda la carpeta `SonelDataExtractor_Portable`
2. Ejecutar `SonelDataExtractor.exe`

> ⚠️ No mover el ejecutable fuera de su carpeta portable.
---

## 📄 Tipos de Archivos Soportados

* `.pqm702` – Power Quality Meter 702
* `.pqm710` – Power Quality Meter 710
* `.pqm711` – Power Quality Meter 711
* `.pqm712` – Power Quality Meter 712

---

## ⚡ Parámetros Eléctricos Procesados

### Mediciones de Voltaje

* Voltaje L1, L2, L3 (RMS)
* Voltaje línea-línea L12

### Mediciones de Corriente

* Corriente L1, L2 (RMS)

### Mediciones de Potencia

* Potencia Activa (P) por fase y total
* Potencia Reactiva (Q) por fase y total
* Potencia Aparente (S) por fase y total
* Potencia Aparente Compleja (Sn) por fase y total

### Datos Temporales

* Timestamp UTC
* Zona UTC
* Fecha
* Hora

---

## 🛡️ Validación y formato de datos

- El script detecta nombres de columnas relevantes de forma flexible
- Se enfoca en la vista de voltaje
- Puedes personalizar los patrones de validación y transformación si tus archivos tienen variantes

---

## 🔍 Solución de problemas

### Error de conexión a la base de datos
- ✅ Verifica que PostgreSQL esté corriendo
- ✅ Confirma credenciales en `.env` o `config.ini`
- ✅ Asegúrate de que la base de datos `sonel_data` exista

### No se encuentran archivos de entrada
- ✅ Confirma que los archivos están en `./data`
- ✅ Verifica que el formato sea compatible

### Fallo en la automatización GUI
- ✅ Asegúrate de tener abierta la aplicación Sonel Analysis
- ✅ Verifica que la interfaz gráfica no haya cambiado
- ✅ Ajusta los tiempos de espera si es necesario

### Formato de archivo no reconocido
- ✅ Revisa los logs generados para más detalles
- ✅ Considera adaptar la lógica de lectura para tu formato específico

### No Qt platform plugin could be initialized
- Asegurar que `qt.conf` esté junto al ejecutable
- No mover el `.exe` fuera de su carpeta
- Instalar **Visual C++ Redistributable**
- Ejecutar como administrador
---

## 📜 Logs y Diagnóstico

### Ubicación

* **Principal:** `logs/sonel_app.log`
* **Rotativos:** `logs/sonel_app.log.1`, `sonel_app.log.2`, etc.

### Niveles de Log

* **DEBUG:** Detalles técnicos
* **INFO:** Operaciones normales
* **WARNING:** Situaciones anómalas recuperables
* **ERROR:** Fallos de procesos
* **CRITICAL:** Errores graves

---

## 🧮 Estructura de Base de Datos

### Tablas Normalizadas

* **codigo:** Información de clientes
* **mediciones:** Registro base
* **voltaje_mediciones:** Datos de voltaje
* **corriente_mediciones:** Datos de corriente
* **potencia_mediciones:** Datos de potencia

### Tabla Desnormalizada

* **mediciones_planas:** Consolidado de análisis

---

## 🤝 Contribución

Este script fue desarrollado con el objetivo de facilitar tareas repetitivas en la gestión y análisis de datos eléctricos. Puedes adaptarlo libremente para tus necesidades.

Si deseas colaborar o tienes sugerencias:
- 🐛 Reporta bugs abriendo un issue
- 💡 Propón mejoras
- 🔧 Envía pull requests

---

📅 **Última actualización:** 03/10/2025

> **Versión Actual:** 1.2.0

---

```
**Desarrollado para automatizar el procesamiento de datos eléctricos con Sonel Analysis** ⚡
```

<div align="center">

**[⬆ Volver al inicio](#-sonel-analysis-data-extractor)**

</div>
