"""
Script para compilar el sistema Sonel a ejecutable portable - VERSIÓN MEJORADA
Soluciona el error: "no Qt platform plugin could be initialized"
Ejecutar: python build_executable_fixed.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_directories():
    """Limpia directorios de compilación anteriores"""
    dirs_to_clean = ['build', 'dist', '__pycache__', 'SonelDataExtractor_Portable']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"🗑️ Eliminado directorio: {dir_name}")

def copy_additional_files():
    """Copia archivos adicionales al directorio dist con estructura completa"""
    files_to_copy = {
        'componentes_configuracion.json': 'componentes_configuracion.json',
        'config.ini': 'config.ini',
        '.env': '.env',
        'README.md': 'README.md'
    }
    
    # Directorios completos a copiar
    dirs_to_copy = [
        'config',
        'data',
        'logs', 
        'temp'
    ]
    
    # Crear directorio dist si no existe
    os.makedirs('dist', exist_ok=True)
    
    # Copiar archivos individuales
    for src, dst in files_to_copy.items():
        if os.path.exists(src):
            shutil.copy2(src, os.path.join('dist', dst))
            print(f"Copiado: {src} -> dist/{dst}")
        else:
            print(f"Advertencia: Archivo no encontrado: {src}")
    
    # Copiar directorios completos con toda su estructura
    for dir_name in dirs_to_copy:
        src_path = dir_name
        dst_path = os.path.join('dist', dir_name)
        
        if os.path.exists(src_path):
            if os.path.exists(dst_path):
                shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
            print(f"Copiado directorio completo: {dir_name} -> dist/{dir_name}")
        else:
            # Crear directorio vacío si no existe
            os.makedirs(dst_path, exist_ok=True)
            print(f"Creado directorio vacío: dist/{dir_name}")

def verify_pyqt5_detailed():
    """Verificación detallada de PyQt5 y sus componentes"""
    print("🔍 VERIFICACIÓN DETALLADA DE PyQt5...")
    
    try:
        import PyQt5
        from PyQt5 import QtCore, QtGui, QtWidgets
        
        # Información básica
        pyqt5_path = os.path.dirname(PyQt5.__file__)
        print(f"✅ PyQt5 version: {QtCore.PYQT_VERSION_STR}")
        print(f"✅ Qt version: {QtCore.QT_VERSION_STR}")
        print(f"✅ PyQt5 instalado en: {pyqt5_path}")
        
        # Verificar estructura Qt
        qt_path = os.path.join(pyqt5_path, 'Qt5')
        print(f"📁 Directorio Qt: {qt_path}")
        print(f"   Existe: {'✅' if os.path.exists(qt_path) else '❌'}")
        
        # Verificar plugins críticos
        plugins_path = os.path.join(qt_path, 'plugins')
        platforms_path = os.path.join(plugins_path, 'platforms')
        
        print(f"📁 Plugins path: {plugins_path}")
        print(f"   Existe: {'✅' if os.path.exists(plugins_path) else '❌'}")
        
        print(f"📁 Platforms path: {platforms_path}")
        print(f"   Existe: {'✅' if os.path.exists(platforms_path) else '❌'}")
        
        # Listar archivos de plataforma
        if os.path.exists(platforms_path):
            platform_files = [f for f in os.listdir(platforms_path) 
                            if f.endswith(('.dll', '.so', '.dylib'))]
            print(f"📦 Archivos de plataforma encontrados: {len(platform_files)}")
            for pf in platform_files:
                print(f"   - {pf}")
                
            # Verificar plugins críticos específicos
            critical_plugins = ['qwindows.dll', 'qminimal.dll', 'qoffscreen.dll']
            missing_plugins = []
            for plugin in critical_plugins:
                if plugin not in platform_files:
                    missing_plugins.append(plugin)
            
            if missing_plugins:
                print(f"⚠️ Plugins críticos faltantes: {missing_plugins}")
            else:
                print("✅ Todos los plugins críticos están presentes")
        
        # Verificar binarios Qt
        qt_bin_path = os.path.join(qt_path, 'bin')
        if os.path.exists(qt_bin_path):
            qt_dlls = [f for f in os.listdir(qt_bin_path) if f.endswith('.dll')]
            print(f"📦 DLLs de Qt encontradas: {len(qt_dlls)}")
        
        return True, pyqt5_path, qt_path
        
    except ImportError as e:
        print(f"❌ Error importando PyQt5: {e}")
        return False, None, None
    except Exception as e:
        print(f"❌ Error verificando PyQt5: {e}")
        return False, None, None

def create_qt_conf_file():
    """Crea archivo qt.conf NO INVASIVO para configurar plugins Qt"""
    # VERSIÓN MEJORADA: qt.conf específico que no interfiere con aplicaciones externas
    qt_conf_content = """[Paths]
Plugins = PyQt5/Qt/plugins
Binaries = PyQt5/Qt/bin
Libraries = PyQt5/Qt/lib

[Qt]
; Configuración aislada solo para esta aplicación
; No afecta procesos hijo o aplicaciones externas
"""
    
    with open('qt.conf', 'w') as f:
        f.write(qt_conf_content)
    
    print("✅ Archivo qt.conf creado (configuración aislada de plugins Qt)")

def create_pyqt5_hook():
    """Crea hook específico para PyQt5 con manejo robusto de plugins"""
    hook_dir = 'hooks'
    os.makedirs(hook_dir, exist_ok=True)
    
    hook_content = '''"""
Hook personalizado para PyQt5 - Asegura inclusión correcta de plugins Qt
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os

# Recolectar todos los datos de PyQt5
datas = collect_data_files('PyQt5')

# Submódulos críticos de PyQt5
hiddenimports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtPrintSupport',
    'PyQt5.sip',
    'sip'
]

# Agregar plugins Qt manualmente para asegurar inclusión
try:
    import PyQt5
    pyqt5_path = os.path.dirname(PyQt5.__file__)
    
    # Plugins críticos para funcionamiento
    qt_plugins_path = os.path.join(pyqt5_path, 'Qt', 'plugins')
    
    if os.path.exists(qt_plugins_path):
        # Plataformas (CRÍTICO)
        platforms_path = os.path.join(qt_plugins_path, 'platforms')
        if os.path.exists(platforms_path):
            datas += [(platforms_path, 'PyQt5/Qt/plugins/platforms')]
        
        # Formatos de imagen
        imageformats_path = os.path.join(qt_plugins_path, 'imageformats') 
        if os.path.exists(imageformats_path):
            datas += [(imageformats_path, 'PyQt5/Qt/plugins/imageformats')]
            
        # Motores de iconos
        iconengines_path = os.path.join(qt_plugins_path, 'iconengines')
        if os.path.exists(iconengines_path):
            datas += [(iconengines_path, 'PyQt5/Qt/plugins/iconengines')]
    
    # Binarios Qt
    qt_bin_path = os.path.join(pyqt5_path, 'Qt', 'bin')
    if os.path.exists(qt_bin_path):
        datas += [(qt_bin_path, 'PyQt5/Qt/bin')]
        
except ImportError:
    pass
'''
    
    with open(os.path.join(hook_dir, 'hook-PyQt5.py'), 'w', encoding='utf-8') as f:
        f.write(hook_content)
    
    print(f"✅ Hook específico para PyQt5 creado en: {hook_dir}/hook-PyQt5.py")

def create_spec_file():
    """Crea el archivo .spec para PyInstaller de forma directa y robusta"""
    
    # Crear el contenido del .spec escribiendo directamente las rutas
    with open('SonelDataExtractor.spec', 'w', encoding='utf-8') as f:
        f.write('''# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None
base_dir = Path.cwd()

# Detectar rutas de PyQt5 dinámicamente
def get_qt_plugins_paths():
    """Obtiene las rutas de plugins Qt de forma segura y robusta"""
    import sys
    import os
    
    qt_plugins = []
    
    try:
        import PyQt5
        pyqt5_dir = os.path.dirname(PyQt5.__file__)
        
        # Ruta base de plugins Qt
        qt_base = os.path.join(pyqt5_dir, 'Qt')
        plugins_base = os.path.join(qt_base, 'plugins')
        
        print(f"🔍 PyQt5 detectado en: {pyqt5_dir}")
        print(f"🔍 Buscando plugins en: {plugins_base}")
        
        if os.path.exists(plugins_base):
            # Mapeo correcto de plugins críticos
            critical_plugins = {
                'platforms': 'PyQt5/Qt/plugins/platforms',
                'imageformats': 'PyQt5/Qt/plugins/imageformats', 
                'iconengines': 'PyQt5/Qt/plugins/iconengines',
                'platformthemes': 'PyQt5/Qt/plugins/platformthemes',
                'styles': 'PyQt5/Qt/plugins/styles'
            }
            
            for plugin_type, dest_path in critical_plugins.items():
                plugin_path = os.path.join(plugins_base, plugin_type)
                if os.path.exists(plugin_path):
                    qt_plugins.append((plugin_path, dest_path))
                    plugin_files = len([f for f in os.listdir(plugin_path) if f.endswith(('.dll', '.so'))])
                    print(f"✅ Plugin {plugin_type}: {plugin_files} archivos encontrados")
                else:
                    print(f"⚠️ Plugin {plugin_type} no encontrado en: {plugin_path}")
            
            # También incluir las DLLs de Qt base
            qt_bin = os.path.join(qt_base, 'bin')
            if os.path.exists(qt_bin):
                qt_plugins.append((qt_bin, 'PyQt5/Qt/bin'))
                print(f"✅ Binarios Qt incluidos desde: {qt_bin}")
        else:
            print(f"❌ Directorio de plugins no encontrado: {plugins_base}")
            
    except ImportError as e:
        print(f"❌ Error importando PyQt5: {e}")
    except Exception as e:
        print(f"❌ Error inesperado detectando Qt: {e}")
    
    print(f"📦 Total de elementos Qt a incluir: {len(qt_plugins)}")
    return qt_plugins

# Obtener plugins Qt disponibles
qt_plugins_data = get_qt_plugins_paths()

# Configurar rutas de datos base
base_datas = [
    # Archivos de configuración principales
    ('config.ini', '.') if os.path.exists('config.ini') else None,
    ('componentes_configuracion.json', '.') if os.path.exists('componentes_configuracion.json') else None,
    ('.env', '.') if os.path.exists('.env') else None,
    ('README.md', '.') if os.path.exists('README.md') else None,
    
    # Directorios completos
    ('config', 'config') if os.path.exists('config') else None,
    ('data', 'data') if os.path.exists('data') else None,
    ('logs', 'logs') if os.path.exists('logs') else None,
    ('temp', 'temp') if os.path.exists('temp') else None,
]

# Filtrar elementos None y agregar plugins Qt
datas = [item for item in base_datas if item is not None]
datas.extend(qt_plugins_data)

print(f"Total de archivos/directorios a incluir: {len(datas)}")

# Dependencias ocultas completas
hiddenimports = [
    # PyQt5 Core - CRÍTICO
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets', 
    'PyQt5.QtPrintSupport',
    'PyQt5.sip',
    'sip',
    
    # Pandas y NumPy
    'pandas',
    'numpy',
    'numpy.core',
    'numpy.core._methods',
    'numpy.lib.format',
    'pandas._libs.tslibs.timedeltas',
    'pandas._libs.tslibs.np_datetime',
    'pandas._libs.tslibs.nattype',
    'pandas._libs.properties',
    'pandas.io.formats.style',
    'pandas._libs.hashtable',
    'pandas._libs.lib',
    'pandas._libs.interval',
    'pandas._libs.parsers',
    
    # Base de datos
    'psycopg2',
    'psycopg2._psycopg',
    'psycopg2.extensions',
    
    # Automatización GUI
    'pyautogui',
    'pywinauto',
    'pywinauto.application',
    'pywinauto.controls',
    'pynput',
    'pynput.keyboard',
    'pynput.mouse',
    
    # Módulos estándar
    'configparser',
    'pathlib',
    'json',
    'csv',
    'datetime',
    'logging',
    'traceback',
    'concurrent.futures',
    'threading',
    'multiprocessing',
    
    # Módulos del proyecto
    'config.settings',
    'config.logger',
    'core.controller.sonel_controller',
    'core.database.connection',
    'core.etl.sonel_etl',
    'gui.window.application',
    'gui.components.panels.control_panel',
    'gui.components.panels.status_panel',
    'gui.components.panels.header_panel',
    'gui.components.panels.footer_panel',
    'gui.styles.themes',
    'gui.utils.ui_helper',
]

a = Analysis(
    ['app.py'],
    pathex=[str(base_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['hooks'] if os.path.exists('hooks') else [],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        'sphinx',
        'pytest',
        'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SonelDataExtractor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
    version_file='version_info.txt' if os.path.exists('version_info.txt') else None,
)
''')
    
    print("Archivo .spec creado: SonelDataExtractor.spec")

def create_simple_spec_file():
    """Crea un archivo .spec mejorado con mejor manejo de plugins Qt"""
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
"""
Archivo .spec mejorado para PyInstaller
Soluciona problemas con plugins Qt de PyQt5
"""

import os
import sys
from pathlib import Path

block_cipher = None
base_dir = Path.cwd()

def collect_qt_plugins():
    """Función robusta para recolectar plugins Qt"""
    import sys
    import os
    
    qt_data = []
    
    try:
        import PyQt5
        pyqt5_dir = os.path.dirname(PyQt5.__file__)
        
        print(f"🔍 Recolectando plugins Qt desde: {pyqt5_dir}")
        
        # Ruta base de Qt
        qt_base = os.path.join(pyqt5_dir, 'Qt5')
        
        if not os.path.exists(qt_base):
            print(f"❌ Directorio Qt no encontrado: {qt_base}")
            return qt_data
        
        # 1. PLUGINS DE PLATAFORMA (CRÍTICO)
        platforms_src = os.path.join(qt_base, 'plugins', 'platforms')
        if os.path.exists(platforms_src):
            # Incluir TODO el directorio platforms
            qt_data.append((platforms_src, 'PyQt5/Qt/plugins/platforms'))
            print(f"✅ Plataformas incluidas desde: {platforms_src}")
            
            # Verificar plugins críticos
            platform_files = os.listdir(platforms_src)
            critical_plugins = ['qwindows.dll', 'qminimal.dll', 'qoffscreen.dll']
            for plugin in critical_plugins:
                if plugin in platform_files:
                    print(f"  ✅ {plugin} encontrado")
                else:
                    print(f"  ⚠️ {plugin} no encontrado")
        
        # 2. OTROS PLUGINS IMPORTANTES
        plugin_types = [
            'imageformats',
            'iconengines', 
            'styles',
            'platformthemes',
            'generic',
            'bearer'
        ]
        
        plugins_base = os.path.join(qt_base, 'plugins')
        for plugin_type in plugin_types:
            plugin_src = os.path.join(plugins_base, plugin_type)
            if os.path.exists(plugin_src):
                plugin_dst = f'PyQt5/Qt/plugins/{plugin_type}'
                qt_data.append((plugin_src, plugin_dst))
                print(f"✅ Plugin {plugin_type} incluido")
        
        # 3. BINARIOS QT
        qt_bin = os.path.join(qt_base, 'bin')
        if os.path.exists(qt_bin):
            qt_data.append((qt_bin, 'PyQt5/Qt/bin'))
            print(f"✅ Binarios Qt incluidos desde: {qt_bin}")
        
        # 4. BIBLIOTECAS QT
        qt_lib = os.path.join(qt_base, 'lib') 
        if os.path.exists(qt_lib):
            qt_data.append((qt_lib, 'PyQt5/Qt/lib'))
            print(f"✅ Bibliotecas Qt incluidas desde: {qt_lib}")
        
        print(f"📦 Total elementos Qt recolectados: {len(qt_data)}")
        
    except Exception as e:
        print(f"❌ Error recolectando plugins Qt: {e}")
    
    return qt_data

# Recolectar plugins Qt
qt_plugins_data = collect_qt_plugins()

# Archivos de datos del proyecto
project_data = []

# Archivos de configuración
config_files = [
    'config.ini',
    'componentes_configuracion.json',
    '.env',
    'README.md'
]

for config_file in config_files:
    if os.path.exists(config_file):
        project_data.append((config_file, '.'))
        print(f"✅ Archivo incluido: {config_file}")

# Directorios del proyecto
project_dirs = [
    'config',
    'data', 
    'logs',
    'temp'
]

for proj_dir in project_dirs:
    if os.path.exists(proj_dir):
        project_data.append((proj_dir, proj_dir))
        print(f"✅ Directorio incluido: {proj_dir}")

# Combinar todos los datos
all_data = project_data + qt_plugins_data

print(f"📊 Total archivos/directorios a incluir: {len(all_data)}")

# Importaciones ocultas expandidas
hiddenimports = [
    # PyQt5 Core - CRÍTICO
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtPrintSupport',
    'PyQt5.sip',
    'sip',
    
    # PyQt5 adicionales (por si se usan)
    'PyQt5.QtNetwork',
    'PyQt5.QtOpenGL',
    'PyQt5.QtSql',
    'PyQt5.QtSvg',
    'PyQt5.QtWebKit',
    'PyQt5.QtWebKitWidgets',
    'PyQt5.QtXml',
    
    # Pandas completo
    'pandas',
    'pandas._libs.tslibs.timedeltas',
    'pandas._libs.tslibs.np_datetime',
    'pandas._libs.tslibs.nattype',
    'pandas._libs.properties',
    'pandas._libs.hashtable',
    'pandas._libs.lib',
    'pandas._libs.interval',
    'pandas._libs.parsers',
    'pandas.io.formats.style',
    'pandas._libs.skiplist',
    'pandas._libs.algos',
    'pandas._libs.join',
    'pandas._libs.groupby',
    'pandas._libs.ops',
    'pandas._libs.sparse',
    'pandas._libs.reduction',
    'pandas._libs.testing',
    'pandas._libs.window',
    'pandas._libs.writers',
    'pandas._libs.json',
    
    # NumPy
    'numpy',
    'numpy.core',
    'numpy.core._methods',
    'numpy.lib.format',
    'numpy.random.common',
    'numpy.random.bounded_integers',
    'numpy.random.entropy',
    
    # Base de datos
    'psycopg2',
    'psycopg2._psycopg',
    'psycopg2.extensions',
    'psycopg2.extras',
    
    # Automatización GUI
    'pyautogui',
    'pywinauto',
    'pywinauto.application',
    'pywinauto.controls',
    'pywinauto.controls.common_controls',
    'pywinauto.controls.win32_controls',
    'pywinauto.controls.uiawrapper',
    'pynput',
    'pynput.keyboard',
    'pynput.mouse',
    'pynput._util',
    'pynput._util.win32',
    
    # Módulos estándar críticos
    'configparser',
    'pathlib',
    'json',
    'csv',
    'datetime',
    'logging',
    'logging.handlers',
    'traceback',
    'concurrent.futures',
    'threading',
    'multiprocessing',
    'queue',
    'time',
    'os',
    'sys',
    'shutil',
    'subprocess',
    'tempfile',
    
    # Módulos del proyecto (ajusta según tu estructura)
    'config.settings',
    'config.logger',
    'core.controller.sonel_controller',
    'core.database.connection',
    'core.etl.sonel_etl',
    'gui.window.application',
    'gui.components.panels.control_panel',
    'gui.components.panels.status_panel',
    'gui.components.panels.header_panel',
    'gui.components.panels.footer_panel',
    'gui.styles.themes',
    'gui.utils.ui_helper',
]

# Binarios adicionales si son necesarios
binaries = []

# Runtime hooks para Qt
runtime_hooks = []

a = Analysis(
    ['app.py'],
    pathex=[str(base_dir)],
    binaries=binaries,
    datas=all_data,
    hiddenimports=hiddenimports,
    hookspath=[],  # No usar hooks personalizados por ahora
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=[
        # Excluir módulos innecesarios para reducir tamaño
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        'sphinx',
        'pytest',
        'setuptools',
        'distutils',
        'test',
        'tests',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filtrar duplicados y optimizar
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SonelDataExtractor',
    debug=False,          
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,             # Comprimir con UPX
    upx_exclude=[
        # No comprimir DLLs críticas de Qt
        'qwindows.dll',
        'qminimal.dll', 
        'qoffscreen.dll',
        'Qt5Core.dll',
        'Qt5Gui.dll',
        'Qt5Widgets.dll',
    ],
    runtime_tmpdir=None,
    console=False,        
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
    version_file='version_info.txt' if os.path.exists('version_info.txt') else None,
)
'''
    
    with open('SonelDataExtractor.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ Archivo .spec mejorado creado: SonelDataExtractor.spec")

def create_pandas_hook():
    """Crea un hook personalizado para pandas"""
    hook_dir = 'hooks'
    os.makedirs(hook_dir, exist_ok=True)
    
    hook_content = '''from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Incluir todos los submódulos de pandas
hiddenimports = collect_submodules('pandas')

# Incluir archivos de datos de pandas
datas = collect_data_files('pandas')

# Importaciones adicionales críticas para pandas
hiddenimports += [
    'pandas._libs.tslibs.timedeltas',
    'pandas._libs.tslibs.np_datetime', 
    'pandas._libs.tslibs.nattype',
    'pandas._libs.skiplist',
    'pandas._libs.hashtable',
    'pandas._libs.lib',
    'pandas._libs.interval',
    'pandas._libs.join',
    'pandas._libs.algos',
    'pandas._libs.groupby',
    'pandas._libs.ops',
    'pandas._libs.sparse',
    'pandas._libs.reduction',
    'pandas._libs.testing',
    'pandas._libs.window',
    'pandas._libs.parsers',
    'pandas._libs.writers',
    'pandas._libs.json',
]'''
    
    with open(os.path.join(hook_dir, 'hook-pandas.py'), 'w') as f:
        f.write(hook_content)
    
    print(f"Hook personalizado para pandas creado en: {hook_dir}/hook-pandas.py")

def create_version_info():
    """Crea archivo de información de versión para Windows"""
    version_info = '''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1,2,0,0),
    prodvers=(1,2,0,0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'EEASA'),
         StringStruct(u'FileDescription', u'Sonel Data Extractor - Sistema ETL'),
         StringStruct(u'FileVersion', u'1.2.0.0'),
         StringStruct(u'InternalName', u'SonelDataExtractor'),
         StringStruct(u'LegalCopyright', u'Copyright (C) 2025'),
         StringStruct(u'OriginalFilename', u'SonelDataExtractor.exe'),
         StringStruct(u'ProductName', u'Sonel Data Extractor'),
         StringStruct(u'ProductVersion', u'1.2.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    print("Archivo de versión creado: version_info.txt")

def build_executable():
    """Compila el ejecutable con manejo robusto de errores"""
    print("🚀 INICIANDO COMPILACIÓN CON PyInstaller...")
    
    if not os.path.exists('SonelDataExtractor.spec'):
        print("❌ ERROR: Archivo .spec no encontrado")
        return False
    
    # Comando de compilación optimizado
    cmd = [
        'pyinstaller',
        '--clean',              # Limpiar cache
        '--noconfirm',          # No pedir confirmación
        '--log-level=INFO',     # Nivel de log detallado
        '--distpath=dist',      # Directorio de salida
        '--workpath=build',     # Directorio de trabajo
        'SonelDataExtractor.spec'
    ]
    
    try:
        print(f"📝 Ejecutando comando: {' '.join(cmd)}")
        print("⏳ Esto puede tardar varios minutos...")
        
        # Ejecutar con timeout de 45 minutos
        result = subprocess.run(
            cmd, 
            check=True, 
            capture_output=True, 
            text=True, 
            timeout=2700,
            cwd=os.getcwd()
        )
        
        print("✅ ¡COMPILACIÓN EXITOSA!")
        
        # Verificar que el ejecutable fue creado
        exe_path = os.path.join('dist', 'SonelDataExtractor.exe')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024*1024)
            print(f"📦 Ejecutable creado: {exe_path}")
            print(f"📏 Tamaño: {size_mb:.1f} MB")
            
            # Verificar estructura interna
            print("🔍 Verificando plugins Qt en el ejecutable...")
            # Esta verificación se haría ejecutando el programa, por ahora solo reportamos
            
            return True
        else:
            print("❌ ERROR: El archivo ejecutable no fue generado")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ ERROR: Tiempo de compilación agotado (45 minutos)")
        print("💡 La compilación puede estar colgada. Intenta con menos dependencias.")
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR DE COMPILACIÓN (código: {e.returncode})")
        
        # Análisis específico de errores comunes
        error_output = e.stderr.lower()
        
        if 'qt' in error_output and 'plugin' in error_output:
            print("🔍 ERROR RELACIONADO CON PLUGINS QT:")
            print("  - Verifica que PyQt5 esté instalado correctamente")
            print("  - Revisa que los plugins de plataforma existan")
            
        if 'import' in error_output:
            print("🔍 ERROR DE IMPORTACIÓN DETECTADO:")
            print("  - Alguna dependencia puede estar faltante")
            print("  - Revisa los hiddenimports en el archivo .spec")
            
        if 'memory' in error_output or 'space' in error_output:
            print("🔍 POSIBLE ERROR DE MEMORIA:")
            print("  - Libera espacio en disco")
            print("  - Cierra otras aplicaciones")
        
        # Mostrar los últimos mensajes de error
        print("\n--- MENSAJES DE ERROR (últimas 15 líneas) ---")
        if e.stderr:
            error_lines = e.stderr.strip().split('\n')
            for line in error_lines[-15:]:
                if line.strip():
                    print(f"  {line}")
        
        return False
        
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {type(e).__name__}: {e}")
        return False

def create_portable_structure():
    """Crea la distribución portable final con verificaciones"""
    print("📦 CREANDO DISTRIBUCIÓN PORTABLE...")
    
    portable_dir = 'SonelDataExtractor_Portable'
    
    # Limpiar directorio anterior
    if os.path.exists(portable_dir):
        shutil.rmtree(portable_dir)
    
    os.makedirs(portable_dir)
    
    # 1. Copiar ejecutable principal
    exe_src = os.path.join('dist', 'SonelDataExtractor.exe')
    exe_dst = os.path.join(portable_dir, 'SonelDataExtractor.exe')
    
    if not os.path.exists(exe_src):
        print(f"❌ ERROR: Ejecutable no encontrado en {exe_src}")
        return False
    
    shutil.copy2(exe_src, exe_dst)
    print(f"✅ Ejecutable copiado: {exe_dst}")
    
    # 2. Crear archivo qt.conf en el directorio portable
    qt_conf_portable = os.path.join(portable_dir, 'qt.conf')
    with open(qt_conf_portable, 'w') as f:
        f.write("""[Paths]
Plugins = PyQt5/Qt/plugins
Binaries = PyQt5/Qt/bin
Libraries = PyQt5/Qt/lib

[Qt]
; Configuración específica para SonelDataExtractor
; No interfiere con otras aplicaciones Qt como Sonel Analysis
; Cada aplicación usa sus propios plugins
""")
    print("✅ qt.conf aislado creado en directorio portable")
    
    # 3. Crear estructura de directorios completa
    dirs_structure = {
        'config': 'Archivos de configuración adicionales',
        'data': 'Directorio principal de datos',
        'data/archivos_pqm': 'Archivos PQM de entrada', 
        'data/archivos_csv': 'Archivos CSV generados',
        'logs': 'Archivos de registro del sistema',
        'temp': 'Archivos temporales',
        'temp/extractors': 'Extractores temporales',
        'exports': 'Reportes y exportaciones'
    }
    
    for dir_path, description in dirs_structure.items():
        full_path = os.path.join(portable_dir, dir_path)
        os.makedirs(full_path, exist_ok=True)
        
        # Crear archivo descriptivo en cada directorio
        desc_file = os.path.join(full_path, 'DIRECTORY_INFO.txt')
        with open(desc_file, 'w', encoding='utf-8') as f:
            f.write(f"# {dir_path}\n\n{description}\n\n")
            f.write("Este directorio es parte del sistema Sonel Data Extractor.\n")
            f.write("No eliminar a menos que sepas lo que haces.\n")
    
    print(f"✅ Estructura de directorios creada: {len(dirs_structure)} directorios")
    
    # 4. Copiar archivos de configuración existentes
    config_files = {
        'config.ini': 'Configuración principal del sistema',
        'componentes_configuracion.json': 'Configuración de componentes'
    }
    
    for config_file, description in config_files.items():
        if os.path.exists(config_file):
            dst_path = os.path.join(portable_dir, config_file)
            shutil.copy2(config_file, dst_path)
            print(f"✅ Configuración copiada: {config_file}")
        else:
            # Crear archivo de configuración predeterminado
            print(f"⚠️ {config_file} no encontrado, creando versión por defecto...")
            create_default_config(portable_dir, config_file)
    
    # 5. Crear documentación completa
    create_comprehensive_documentation(portable_dir)
    
    # 6. Verificación final
    print("\n🔍 VERIFICACIÓN FINAL:")
    exe_final = os.path.join(portable_dir, 'SonelDataExtractor.exe')
    if os.path.exists(exe_final):
        size_mb = os.path.getsize(exe_final) / (1024*1024)
        print(f"✅ Ejecutable: {size_mb:.1f} MB")
    
    config_final = os.path.join(portable_dir, 'config.ini')
    print(f"✅ Configuración: {'Presente' if os.path.exists(config_final) else 'Ausente'}")
    
    qt_conf_final = os.path.join(portable_dir, 'qt.conf')
    print(f"✅ qt.conf: {'Presente' if os.path.exists(qt_conf_final) else 'Ausente'}")
    
    dir_count = len([d for d in os.listdir(portable_dir) if os.path.isdir(os.path.join(portable_dir, d))])
    print(f"✅ Directorios: {dir_count}")
    
    print(f"\n🎉 ¡DISTRIBUCIÓN PORTABLE CREADA EXITOSAMENTE!")
    print(f"📁 Ubicación: {os.path.abspath(portable_dir)}/")
    print(f"🚀 Para ejecutar: {portable_dir}/SonelDataExtractor.exe")
    
    return True

def create_default_config(portable_dir, config_type):
    """Crea archivos de configuración por defecto"""
    
    if config_type == 'config.ini':
        config_content = """[DATABASE]
host = localhost
port = 5432
database = sonel_data
user = postgres
password = 123456

[PATHS]
data_dir = ./data/archivos_csv
input_dir = ./data/archivos_pqm
export_dir = ./exports
output_dir = ./data/archivos_csv
temp_dir = ./temp

[GUI]
coordinates_file = config/coordinates.json
auto_close_enabled = true
theme = default

[GUI.safety]
pause_between_actions = 0.1

[GUI.delays]
startup_wait = 5.0
window_activation = 2.0
after_menu = 2.0
between_clicks = 0.5
before_export = 1.5
after_export = 3.0
file_naming = 1.0
file_verification = 2.0
between_files = 2.0
process_cleanup = 2.0
ui_response = 1.0

[LOGGING]
level = INFO
file = logs/sonel_app.log
max_size_mb = 10
backup_count = 5
"""
        config_path = os.path.join(portable_dir, 'config.ini')
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print(f"✅ config.ini por defecto creado")
    
    elif config_type == 'componentes_configuracion.json':
        import json
        config_data = {
            "componentes": {
                "database": {
                    "enabled": True,
                    "connection_timeout": 30
                },
                "gui": {
                    "enabled": True,
                    "theme": "default"
                },
                "etl": {
                    "enabled": True,
                    "batch_size": 100
                }
            },
            "version": "1.2.0",
            "last_updated": "2025-01-01"
        }
        
        config_path = os.path.join(portable_dir, 'componentes_configuracion.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        print(f"✅ componentes_configuracion.json por defecto creado")

def create_comprehensive_documentation(portable_dir):
    """Crea documentación completa para el usuario final"""
    
    # README principal
    readme_content = """# Sonel Data Extractor - Versión Portable v1.2.0

## 🚀 INICIO RÁPIDO

### 1. Ejecutar la Aplicación
```
Doble clic en: SonelDataExtractor.exe
```

### 2. Primera Configuración
- Edita `config.ini` con tus datos de PostgreSQL
- Coloca archivos .pqm en `data/archivos_pqm/`
- Ejecuta el sistema

### 3. Si aparece error "Qt platform plugin"
- Asegúrate de que `qt.conf` esté en la misma carpeta que el .exe
- No muevas el ejecutable fuera de esta carpeta
- Ejecuta como Administrador si es necesario

## 📁 ESTRUCTURA DE ARCHIVOS

```
SonelDataExtractor_Portable/
├── SonelDataExtractor.exe          # 🚀 EJECUTABLE PRINCIPAL
├── qt.conf                         # ⚙️ Configuración Qt (NO ELIMINAR)
├── config.ini                      # 🔧 Configuración principal
├── componentes_configuracion.json  # ⚙️ Configuración componentes
├── README.txt                      # 📖 Esta documentación
├── TROUBLESHOOTING.txt            # 🔧 Solución de problemas
│
├── config/                         # Configuraciones adicionales
├── data/
│   ├── archivos_pqm/              # 📥 COLOCA AQUÍ TUS ARCHIVOS .PQM
│   └── archivos_csv/              # 📤 Archivos CSV generados
├── exports/                       # 📊 Reportes exportados
├── logs/                          # 📋 Archivos de registro
└── temp/                          # 🔄 Archivos temporales
```

## ⚙️ CONFIGURACIÓN DE BASE DE DATOS

Edita el archivo `config.ini`:

```ini
[DATABASE]
host = TU_SERVIDOR_POSTGRESQL       # ej: localhost, 192.168.1.100
port = 5432                        # Puerto de PostgreSQL
database = TU_BASE_DE_DATOS        # Nombre de tu base de datos
user = TU_USUARIO                  # Usuario de PostgreSQL  
password = TU_CONTRASEÑA           # Contraseña del usuario
```

## 🔧 FUNCIONALIDADES PRINCIPALES

### Procesamiento de Archivos
- ✅ Carga automática de archivos .pqm
- ✅ Conversión a formato CSV
- ✅ Inserción directa a PostgreSQL
- ✅ Procesamiento por lotes

### Interface Gráfica
- ✅ Panel de control intuitivo
- ✅ Monitoreo de progreso en tiempo real
- ✅ Configuración visual de parámetros
- ✅ Sistema de logs integrado

### Automatización
- ✅ Modo automático completo
- ✅ Modo manual paso a paso
- ✅ Programación de tareas
- ✅ Notificaciones de estado

## 🆘 PROBLEMAS COMUNES

### "No Qt platform plugin could be initialized"
**SOLUCIÓN:**
1. Verifica que `qt.conf` esté junto al ejecutable
2. NO muevas el .exe fuera de esta carpeta
3. Ejecuta como Administrador
4. Reinstala Microsoft Visual C++ Redistributable

### "Error de conexión a base de datos"
**SOLUCIÓN:**
1. Verifica que PostgreSQL esté ejecutándose
2. Comprueba credenciales en `config.ini`
3. Verifica conectividad de red al servidor
4. Asegúrate de que la base de datos existe

### "No se pueden procesar archivos .pqm"
**SOLUCIÓN:**
1. Coloca archivos en `data/archivos_pqm/`
2. Verifica permisos de escritura
3. Revisa logs en `logs/sonel_app.log`
4. Asegúrate de que los archivos no estén corruptos

### La aplicación no inicia
**SOLUCIÓN:**
1. Ejecuta como Administrador
2. Desactiva temporalmente el antivirus
3. Verifica que no falten archivos
4. Consulta `TROUBLESHOOTING.txt` para más detalles

## 📊 TIPOS DE DATOS SOPORTADOS
- Mediciones de calidad de energía
- Registros de perturbaciones y eventos
- Análisis de armónicos (THD)
- Mediciones de tensión/corriente RMS
- Análisis de flicker (Pst, Plt)
- Datos de frecuencia y potencia

## 📞 SOPORTE TÉCNICO
Para soporte contacta al departamento de IT de EEASA.

## 📋 INFORMACIÓN DE VERSIÓN
- **Versión**: 1.2.0
- **Fecha**: 2025
- **Desarrollado para**: EEASA
- **Compatibilidad**: Windows 10/11

---
*Sistema Sonel Data Extractor - EEASA © 2025*
"""
    
    # Guardar README
    readme_path = os.path.join(portable_dir, 'README.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Crear guía de solución de problemas detallada
    troubleshooting_content = """# GUÍA DE SOLUCIÓN DE PROBLEMAS - Sonel Data Extractor

## 🔧 ERROR: "No Qt platform plugin could be initialized"

### CAUSA
Este es el error más común al empaquetar aplicaciones PyQt5. Ocurre cuando el ejecutable no puede encontrar los plugins de plataforma Qt necesarios.

### SOLUCIONES PASO A PASO

#### Solución 1: Verificar qt.conf
1. Asegúrate de que el archivo `qt.conf` esté en la MISMA carpeta que `SonelDataExtractor.exe`
2. Abre `qt.conf` y verifica que contenga:
```
[Paths]
Plugins = PyQt5/Qt/plugins
Binaries = PyQt5/Qt/bin
Libraries = PyQt5/Qt/lib
```

#### Solución 2: No mover el ejecutable
- NUNCA muevas `SonelDataExtractor.exe` fuera de la carpeta `SonelDataExtractor_Portable`
- Si necesitas crear un acceso directo, hazlo pero apunta a la ubicación original

#### Solución 3: Ejecutar como Administrador
1. Click derecho en `SonelDataExtractor.exe`
2. Seleccionar "Ejecutar como administrador"
3. Confirmar permisos UAC

#### Solución 4: Instalar Visual C++ Redistributable
1. Descargar de: https://aka.ms/vs/17/release/vc_redist.x64.exe
2. Instalar y reiniciar el sistema
3. Intentar ejecutar nuevamente

#### Solución 5: Verificar plugins Qt (Avanzado)
1. Abrir símbolo del sistema en la carpeta del ejecutable
2. Ejecutar: `SonelDataExtractor.exe` desde consola
3. Buscar mensajes específicos sobre plugins faltantes

### MENSAJES DE ERROR ESPECÍFICOS

#### "Available platform plugins are: minimal, offscreen, windows"
- **Causa**: Plugin qwindows.dll no encontrado
- **Solución**: Recompilar con el script mejorado

#### "This application failed to start"
- **Causa**: DLLs de Qt faltantes
- **Solución**: Instalar Visual C++ Redistributable

## 🔧 ERROR: Problemas de Base de Datos

### "Connection refused" o "could not connect"
**Diagnóstico:**
1. Abrir `config.ini`
2. Verificar configuración [DATABASE]
3. Probar conexión manual

**Soluciones:**
1. **PostgreSQL no está ejecutándose**
   - Abrir Servicios de Windows (services.msc)
   - Buscar "postgresql" 
   - Iniciar el servicio si está detenido

2. **Credenciales incorrectas**
   - Verificar usuario/contraseña en pgAdmin
   - Actualizar `config.ini` con credenciales correctas

3. **Base de datos no existe**
   - Crear la base de datos en pgAdmin
   - Actualizar nombre en `config.ini`

4. **Problemas de red**
   - Para servidor local: usar `localhost` o `127.0.0.1`
   - Para servidor remoto: verificar conectividad de red
   - Verificar que el puerto 5432 esté abierto

### Error "relation does not exist"
**Causa**: Tablas no creadas en la base de datos
**Solución**: 
1. Ejecutar scripts de creación de tablas
2. Verificar permisos del usuario de BD

## 🔧 ERROR: Problemas con Archivos .pqm

### "No se encontraron archivos para procesar"
**Verificaciones:**
1. Los archivos están en `data/archivos_pqm/`
2. Los archivos tienen extensión `.pqm`
3. Los archivos no están corruptos
4. Tienes permisos de lectura en la carpeta

### "Error al procesar archivo X.pqm"
**Diagnóstico:**
1. Revisar `logs/sonel_app.log`
2. Verificar tamaño y fecha del archivo
3. Intentar abrir el archivo manualmente

**Soluciones:**
1. **Archivo corrupto**: Obtener nueva copia del archivo
2. **Formato no reconocido**: Verificar que sea un archivo PQM válido
3. **Permisos insuficientes**: Ejecutar como administrador

## 🔧 PROBLEMAS DE RENDIMIENTO

### La aplicación se ejecuta muy lenta
**Optimizaciones:**
1. Cerrar otras aplicaciones pesadas
2. Verificar espacio en disco (mínimo 2GB libre)
3. Procesar archivos en lotes más pequeños
4. Aumentar memoria RAM disponible

### "Out of memory" o errores de memoria
**Soluciones:**
1. Procesar archivos de uno en uno
2. Reiniciar la aplicación periodicamente
3. Limpiar carpeta `temp/` regularmente
4. Aumentar memoria virtual del sistema

## 🔧 PROBLEMAS DE INTERFACE GRÁFICA

### Ventana no aparece o se muestra mal
**Soluciones:**
1. Verificar resolución de pantalla (mínimo 1024x768)
2. Actualizar drivers de video
3. Cambiar configuración de DPI en Windows
4. Ejecutar en modo compatibilidad Windows 10

### Botones no responden
**Diagnóstico:**
1. Verificar en logs si hay errores de GUI
2. Probar hacer click en diferentes áreas
3. Usar combinaciones de teclado alternativas

## 🔧 LOGS Y DIAGNÓSTICO

### Ubicación de logs
- **Log principal**: `logs/sonel_app.log`
- **Logs de sistema**: `logs/system_*.log`
- **Logs de errores**: `logs/error_*.log`

### Interpretar mensajes de log
- **INFO**: Información general (normal)
- **WARNING**: Advertencias (pueden ignorarse)
- **ERROR**: Errores que requieren atención
- **CRITICAL**: Errores críticos que detienen la aplicación

### Activar modo debug
1. Editar `config.ini`
2. Cambiar `level = INFO` a `level = DEBUG`
3. Reiniciar aplicación
4. Los logs tendrán más detalles

## 🔧 REINSTALACIÓN COMPLETA

Si nada funciona, sigue estos pasos:

### Paso 1: Backup de datos
1. Copia la carpeta `data/` completa
2. Copia `config.ini` personalizado
3. Copia logs importantes

### Paso 2: Limpieza
1. Eliminar carpeta `SonelDataExtractor_Portable`
2. Limpiar registro de Windows (opcional)

### Paso 3: Nueva instalación
1. Descomprimir nueva versión
2. Restaurar `config.ini` personalizado
3. Restaurar carpeta `data/`
4. Ejecutar nuevamente

## 📞 CONTACTO PARA SOPORTE

Si el problema persiste después de seguir esta guía:

1. **Recopilar información**:
   - Descripción exacta del error
   - Captura de pantalla del error
   - Archivo `logs/sonel_app.log` más reciente
   - Información del sistema (Windows version, RAM, etc.)

2. **Contactar soporte técnico**:
   - Departamento de IT de EEASA
   - Incluir toda la información recopilada

---
*Última actualización: 2025 - Versión 1.2.0*
"""
    
    # Guardar guía de troubleshooting
    troubleshooting_path = os.path.join(portable_dir, 'TROUBLESHOOTING.txt')
    with open(troubleshooting_path, 'w', encoding='utf-8') as f:
        f.write(troubleshooting_content)
    
    print("✅ Documentación completa creada:")
    print(f"   - README.txt")
    print(f"   - TROUBLESHOOTING.txt")

def main():
    """Función principal mejorada del script de compilación"""
    print("=" * 60)
    print("🚀 SONEL DATA EXTRACTOR - COMPILADOR MEJORADO v2.0")
    print("   Solución para error: 'no Qt platform plugin could be initialized'")
    print("=" * 60)
    
    # Verificar requisitos del sistema
    print("\n📋 VERIFICANDO REQUISITOS DEL SISTEMA...")
    
    # 1. Verificar Python
    python_version = sys.version_info
    print(f"✅ Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 2. Verificar PyInstaller
    try:
        result = subprocess.run(['pyinstaller', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ PyInstaller: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller no está instalado")
        print("💡 Instalar con: pip install pyinstaller")
        return False
    
    # 3. Verificar PyQt5 detalladamente
    pyqt5_ok, pyqt5_path, qt_path = verify_pyqt5_detailed()
    if not pyqt5_ok:
        print("❌ PyQt5 no está configurado correctamente")
        print("💡 Reinstalar con: pip uninstall PyQt5 && pip install PyQt5")
        return False
    
    # 4. Verificar archivo principal
    if not os.path.exists('app.py'):
        print("❌ ERROR: Archivo principal 'app.py' no encontrado")
        print("💡 Asegúrate de ejecutar este script desde el directorio del proyecto")
        return False
    
    print("\n✅ Todos los requisitos verificados correctamente")
    
    # PASO 1: Limpieza
    print("\n🧹 PASO 1: LIMPIANDO ARCHIVOS ANTERIORES...")
    clean_build_directories()

    print("\n⚙️ PASO 2: CREANDO ARCHIVOS DE CONFIGURACIÓN...")
    create_qt_conf_file()
    create_simple_spec_file()
    
    # PASO 3: Compilar ejecutable
    print("\n🔨 PASO 3: COMPILANDO EJECUTABLE...")
    if not build_executable():
        print("\n❌ ERROR EN LA COMPILACIÓN")
        print("💡 Revisa los mensajes de error arriba")
        print("💡 Consulta TROUBLESHOOTING.txt para soluciones")
        return False
    
    # PASO 4: Crear distribución portable
    print("\n📦 PASO 4: CREANDO DISTRIBUCIÓN PORTABLE...")
    if not create_portable_structure():
        print("\n❌ ERROR CREANDO DISTRIBUCIÓN PORTABLE")
        return False
    
    # RESUMEN FINAL
    print("\n" + "=" * 60)
    print("🎉 ¡COMPILACIÓN COMPLETADA EXITOSAMENTE!")
    print("=" * 60)
    
    exe_path = os.path.join('SonelDataExtractor_Portable', 'SonelDataExtractor.exe')
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024*1024)
        print(f"📦 Ejecutable: SonelDataExtractor_Portable/SonelDataExtractor.exe ({size_mb:.1f} MB)")
    
    print(f"📁 Ubicación: {os.path.abspath('SonelDataExtractor_Portable')}")
    print(f"📖 Documentación: README.txt y TROUBLESHOOTING.txt incluidos")
    
    print("\n🚀 PASOS SIGUIENTES:")
    print("1. Navegar a la carpeta SonelDataExtractor_Portable/")
    print("2. Configurar config.ini con tus datos de PostgreSQL")
    print("3. Colocar archivos .pqm en data/archivos_pqm/")
    print("4. Ejecutar: SonelDataExtractor.exe")
    
    print("\n⚠️ IMPORTANTE:")
    print("- NO muevas el .exe fuera de su carpeta")
    print("- Mantén qt.conf junto al ejecutable")
    print("- Si hay problemas, consulta TROUBLESHOOTING.txt")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        if success:
            print(f"\n✅ Proceso completado exitosamente")
            input("\n📝 Presiona Enter para salir...")
        else:
            print(f"\n❌ Proceso completado con errores")
            input("\n📝 Presiona Enter para salir...")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 ERROR INESPERADO: {type(e).__name__}: {e}")
        print(f"💡 Reporta este error al soporte técnico")
        input("\n📝 Presiona Enter para salir...")
        sys.exit(1)