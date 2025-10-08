# ⚡ Sonel Analysis Data Extractor

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://www.postgresql.org)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ChrisitanLP/SonelAnalysis)

Automatización para la extracción, transformación y carga (ETL) de datos eléctricos desde archivos generados por **Sonel Analysis 4.6.6** a una base de datos **PostgreSQL**. Este script permite procesar archivos exportados o, en su defecto, automatizar la interfaz gráfica de la aplicación para obtener datos estructurados, con un enfoque especial en mediciones de **voltaje**.

---

## 📋 Tabla de Contenidos

- [Características principales](#-características-principales)
- [Requisitos previos](#️-requisitos-previos)
- [Instalación](#-instalación)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Configuración](#️-configuración)
- [Preparación de la base de datos](#️-preparación-de-la-base-de-datos)
- [Uso](#-uso)
- [Personalización](#-personalización)
- [Validación y formato de datos](#️-validación-y-formato-de-datos)
- [Solución de problemas](#-solución-de-problemas)
- [Registro de logs](#-registro-de-logs)
- [Limitaciones](#️-limitaciones)
- [Contribución](#-contribución)
- [Licencia](#-licencia)

---

## 📌 Características principales

- ✅ Extracción de datos desde archivos exportados (CSV, Excel, XML, MDB, DAT)
- 🖥️ Automatización de la GUI de **Sonel Analysis** para exportar mediciones
- 🔄 Transformación y validación automática de columnas relevantes
- 🗄️ Carga estructurada a base de datos PostgreSQL
- ⚙️ Configuración flexible mediante `.env` y `config.ini`
- 📊 Registro de logs para monitoreo y diagnóstico

---

## 🛠️ Requisitos previos

- **Python** 3.7 o superior  
- **PostgreSQL** 10 o superior  
- **Sonel Analysis** 4.6.6 instalado (solo si se usará la extracción GUI)  

---

## 📦 Instalación

### 1. Clonar o descargar el proyecto
```bash
git clone <repository-url>
cd sonel-data-extractor
```

### 2. Instalar dependencias
```bash
pip install pandas psycopg2-binary python-dotenv pyautogui pywinauto
```

### 3. Crear estructura de directorios
```bash
mkdir -p data exports
```

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

### Opción 1: Archivo `config.ini` (generado automáticamente)

```ini
[DATABASE]
host = localhost
port = ----
database = sonel
user = ****
password = ****

[PATHS]
data_dir = ./data
export_dir = ./exports
```

### Opción 2: Archivo `.env` (tiene prioridad sobre config.ini)

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

## 🗄️ Preparación de la base de datos

### 1. Crear la base de datos

```sql
CREATE DATABASE sonel_data;
```

> **Nota:** La tabla `voltaje_mediciones` se creará automáticamente al ejecutar el script si no existe.

---

## 🚀 Uso

### Método 1: Extracción desde archivos exportados

1. Coloca tus archivos (`.csv`, `.xlsx`, `.xml`, `.mdb`, `.dat`) en la carpeta `data/`
2. Ejecuta el script:

```bash
python extract_sonel_data.py
```

### Método 2: Automatización de la GUI

1. Asegúrate de que **Sonel Analysis** esté abierto
2. Ejecuta el script en modo GUI:

```bash
python extract_sonel_data.py gui
```

> **⚠️ Importante:** La aplicación Sonel Analysis debe estar abierta y visible antes de ejecutar el modo GUI.

---

## 🔧 Personalización

Puedes modificar el script para adaptarlo a necesidades específicas:

| Componente | Función |
|------------|---------|
| `_validate_columns()` | Ajustar patrones de búsqueda de columnas relevantes |
| `transform_voltage_data()` | Modificar estructura o cálculos |
| `_extract_using_gui()` | Cambiar comportamiento de automatización de interfaz |

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

---

## 📊 Registro de logs

El script genera logs tanto en consola como en el archivo `sonel_extraction.log`. Revisa este archivo si deseas rastrear errores o auditorías de ejecución.

---

## ⚠️ Limitaciones

- La automatización GUI puede ser frágil ante cambios en la interfaz
- El soporte para archivos `.mdb` puede requerir configuración ODBC adicional
- Actualmente el script está optimizado para procesar solo datos de voltaje

---

## 🤝 Contribución

Este script fue desarrollado con el objetivo de facilitar tareas repetitivas en la gestión y análisis de datos eléctricos. Puedes adaptarlo libremente para tus necesidades.

Si deseas colaborar o tienes sugerencias:
- 🐛 Reporta bugs abriendo un issue
- 💡 Propón mejoras
- 🔧 Envía pull requests

---

## 📄 Licencia

Este proyecto está disponible bajo la licencia que consideres apropiada para tu caso de uso.

---

**Desarrollado para automatizar el procesamiento de datos eléctricos con Sonel Analysis** ⚡

<div align="center">

**[⬆ Volver al inicio](#-sonel-analysis-data-extractor)**

</div>
