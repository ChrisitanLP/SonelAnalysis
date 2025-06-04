Configuración y uso del script de extracción de datos Sonel Analysis
Este archivo README proporciona instrucciones para configurar y ejecutar el script de extracción de datos de Sonel Analysis 4.6.6.
Requisitos previos

Python 3.7 o superior
PostgreSQL 10 o superior
Sonel Analysis 4.6.6 instalado (opcional si se tienen archivos de datos)

Instalación de dependencias
bashpip install pandas psycopg2-binary python-dotenv pyautogui pywinauto
Estructura de archivos
El script requiere la siguiente estructura de directorios:
sonel_extraction/
├── extract_sonel_data.py  # Script principal
├── config.ini            # Archivo de configuración
├── .env                  # Variables de entorno (opcional)
├── data/                 # Directorio para archivos de datos
└── exports/              # Directorio para exportaciones de la GUI
Cree los directorios necesarios:
bashmkdir -p data exports
Configuración
Archivo config.ini
El script generará automáticamente un archivo config.ini con valores predeterminados si no existe. Puede modificar este archivo según sus necesidades:
ini[DATABASE]
host = localhost
port = 5432
database = sonel_data
user = postgres
password = postgres

[PATHS]
data_dir = ./data
export_dir = ./exports
Variables de entorno (opcional)
Alternativamente, puede crear un archivo .env con las siguientes variables:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sonel_data
DB_USER=postgres
DB_PASSWORD=micontraseña
DATA_DIR=./data
EXPORT_DIR=./exports
Las variables de entorno tienen prioridad sobre la configuración en config.ini.
Preparación de la base de datos

Cree una base de datos en PostgreSQL:

sqlCREATE DATABASE sonel_data;

El script creará automáticamente la tabla voltaje_mediciones si no existe.

Métodos de extracción
El script puede extraer datos de dos formas:
1. Extracción desde archivos
Coloque los archivos de datos exportados de Sonel Analysis en el directorio data/. El script intentará detectar y leer archivos en los siguientes formatos:

CSV
Excel (.xlsx)
XML
MDB (Microsoft Access)
DAT

2. Automatización de GUI
Si no dispone de archivos exportados, el script puede automatizar la interfaz de usuario de Sonel Analysis para exportar los datos. Este método:

Conecta con la aplicación Sonel Analysis
Navega a la sección "Measurements"
Selecciona la vista de voltaje
Exporta los datos a CSV
Lee el archivo exportado

Ejecución del script
Para ejecutar el script con extracción desde archivos (método predeterminado):
bashpython extract_sonel_data.py
Para especificar el método de extracción mediante GUI:
bashpython extract_sonel_data.py gui
Solución de problemas
Registros (Logs)
El script genera registros en:

La salida estándar (terminal)
Un archivo sonel_extraction.log

Consulte estos registros para diagnosticar problemas.
Problemas comunes

Error de conexión a la base de datos:

Verifique que PostgreSQL esté en ejecución
Confirme las credenciales en config.ini o .env
Asegúrese de que la base de datos sonel_data exista


No se encuentran archivos de datos:

Verifique que los archivos estén en la ruta configurada en data_dir
Confirme que los archivos tienen un formato soportado


Errores en la automatización GUI:

Asegúrese de que Sonel Analysis esté abierto antes de ejecutar el script
Verifique que la interfaz no haya cambiado (las automatizaciones GUI son frágiles)
Ajuste los tiempos de espera si es necesario


Formato de datos inesperado:

El script intenta manejar diferentes formatos, pero puede requerir ajustes según el formato específico de sus datos
Revise los registros para identificar problemas específicos



Personalización
Puede modificar el script para adaptarlo a sus necesidades específicas:

Ajustar los patrones de búsqueda de columnas en el método _validate_columns()
Modificar la lógica de transformación en transform_voltage_data()
Ajustar la secuencia de automatización GUI en _extract_using_gui()

Limitaciones

La automatización GUI es frágil y puede fallar si la interfaz cambia
El soporte para archivos MDB requiere configuración ODBC adicional
El script está diseñado para extraer solo datos de voltaje según lo especificado

Modos de Operación Flexibles

# Flujo completo (extracción + procesamiento)
python sonel_integrated_main.py

# Solo extracción GUI
python sonel_integrated_main.py --extract-only

# Solo procesamiento ETL
python sonel_integrated_main.py --process-only

# Con modo debug
python sonel_integrated_main.py --debug

# Forzar reprocesamiento
python sonel_integrated_main.py --force

Opciones:
    --extract-only        Solo ejecutar extracción GUI
    --process-only        Solo ejecutar procesamiento ETL
    --force               Forzar reprocesamiento de archivos
    --debug               Activar modo debug
    --help                Mostrar esta ayuda

Flujo de trabajo:
1. Extracción GUI: Procesa archivos .pqm702 → genera archivos CSV
2. Validación: Verifica que los archivos CSV se hayan generado correctamente
3. Procesamiento ETL: Carga los archivos CSV a la base de datos
4. Limpieza: Opcionalmente mueve/archiva archivos procesados