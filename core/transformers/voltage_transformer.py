#sonel_extractor/transformer/voltage_transformer.py
import re
import numpy as np
import pandas as pd
from config.logger import logger
from core.utils.validators import validate_voltage_columns

class VoltageTransformer:
    """Clase para transformar datos de voltaje al formato requerido"""
    
    @staticmethod
    def transform(data):
        """
        Transforma los datos de voltaje al formato requerido
        
        Args:
            data: DataFrame con los datos extraídos
            
        Returns:
            DataFrame transformado
        """
        if data is None or data.empty:
            logger.error("No hay datos para transformar")
            return None
            
        logger.info("Iniciando transformación de datos")
        
        try:
            # Copia para no modificar el original
            df = data.copy()

            # Imprimir las columnas disponibles para debug
            logger.info(f"Columnas disponibles en el DataFrame original: {list(df.columns)}")
            
            # Identificar columnas usando la función mejorada
            valid, column_map = validate_voltage_columns(df)
            if not valid or not column_map:
                logger.error("No se pudieron identificar las columnas necesarias para la transformación")
                return None
            
            # Imprimir el mapeo de columnas para debug
            logger.info(f"Mapeo de columnas identificado: {column_map}")
            
            # Crear nuevo DataFrame con las columnas requeridas
            transformed_df = pd.DataFrame()
            
            # Convertir columna de tiempo
            time_col = column_map.get('time')
            if time_col:
                try:
                    # Manejar posibles formatos de fecha/hora combinados
                    if df[time_col].dtype == object:
                        # Comprobar si hay columnas separadas para fecha y hora
                        date_col = None
                        for col in df.columns:
                            if re.search(r'(?i)fecha|date', col) and col != time_col:
                                date_col = col
                                break
                        
                        if date_col and re.search(r'(?i)hora|time', time_col):
                            # Combinar fecha y hora si están separadas
                            date_time = df[date_col].astype(str) + ' ' + df[time_col].astype(str)
                            transformed_df['tiempo_utc'] = pd.to_datetime(date_time, errors='coerce')
                        else:
                            # Intentar diferentes formatos de fecha/hora
                            for date_format in ['%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S']:
                                try:
                                    transformed_df['tiempo_utc'] = pd.to_datetime(df[time_col], format=date_format)
                                    break
                                except:
                                    continue
                            
                            # Si los formatos anteriores fallan, usar el parser automático
                            if 'tiempo_utc' not in transformed_df.columns:
                                transformed_df['tiempo_utc'] = pd.to_datetime(df[time_col], errors='coerce')
                    else:
                        # Probablemente ya es datetime
                        transformed_df['tiempo_utc'] = df[time_col]
                except Exception as e:
                    logger.error(f"Error al convertir columna de tiempo: {e}")
                    # Usar el valor original como fallback
                    transformed_df['tiempo_utc'] = df[time_col]
            else:
                logger.error("No se encontró columna de tiempo para la transformación")
                return None
            
            # Función auxiliar para convertir valores a numéricos
            def convert_to_numeric(df, source_col):
                if source_col is None:
                    return None
                
                try:
                    if df[source_col].dtype == object:  # Si es string
                        # Extraer valores numéricos del texto incluyendo el signo negativo
                        # Patrón mejorado para capturar: signo opcional + dígitos + punto decimal opcional + más dígitos
                        values = df[source_col].astype(str).str.replace(',', '.').str.extract(r'(-?[\d\.]+)')[0]
                        return pd.to_numeric(values, errors='coerce')
                    else:
                        # Ya es numérico
                        return df[source_col]
                except Exception as e:
                    logger.debug(f"Error al transformar columna {source_col}: {e}")
                    return None

            # Convertir columnas de voltaje
            voltage_columns = {
                'u_l1_avg_10min': column_map.get('u_l1'),
                'u_l2_avg_10min': column_map.get('u_l2'),
                'u_l3_avg_10min': column_map.get('u_l3'),
                'u_l12_avg_10min': column_map.get('u_l12')
            }
            
            for target_col, source_col in voltage_columns.items():
                transformed_df[target_col] = convert_to_numeric(df, source_col)
            
            # Agregar columnas para corriente
            current_columns = {
                'i_l1_avg': column_map.get('i_l1'),
                'i_l2_avg': column_map.get('i_l2')
            }
            
            for target_col, source_col in current_columns.items():
                transformed_df[target_col] = convert_to_numeric(df, source_col)
            
            # Agregar columnas para potencia
            power_columns = {
                'p_l1_avg': column_map.get('p_l1'),
                'p_l2_avg': column_map.get('p_l2'),
                'p_l3_avg': column_map.get('p_l3'),
                'p_e_avg': column_map.get('p_e'),
                'q1_l1_avg': column_map.get('q1_l1'),
                'q1_l2_avg': column_map.get('q1_l2'),
                'q1_e_avg': column_map.get('q1_e'),
                'sn_l1_avg': column_map.get('sn_l1'),
                'sn_l2_avg': column_map.get('sn_l2'),
                'sn_e_avg': column_map.get('sn_e'),
                's_l1_avg': column_map.get('s_l1'),
                's_l2_avg': column_map.get('s_l2'),
                's_e_avg': column_map.get('s_e')
            }
            
            for target_col, source_col in power_columns.items():
                transformed_df[target_col] = convert_to_numeric(df, source_col)
                
                # Si la columna no se encontró o está vacía, asegurar que existe con valores NaN
                if target_col not in transformed_df.columns or transformed_df[target_col].isnull().all():
                    transformed_df[target_col] = np.nan
                    logger.debug(f"Columna {target_col} no encontrada, establecida como NaN")
            
            # Verificar que las columnas de potencia existan y tengan valores
            power_cols_present = [col for col in power_columns.keys() if col in transformed_df.columns]
            if power_cols_present:
                has_power_data = any(not transformed_df[col].isnull().all() for col in power_cols_present)
                if has_power_data:
                    logger.info("Se han encontrado datos de potencia en el archivo")
                else:
                    logger.warning("Las columnas de potencia existen pero no contienen datos")
            else:
                logger.warning("No se encontraron columnas de potencia en el archivo")
            
            logger.info("Transformación de datos completada exitosamente")
            logger.info(f"Columnas en el DataFrame transformado: {list(transformed_df.columns)}")
            return transformed_df
            
        except Exception as e:
            logger.error(f"Error durante la transformación de datos: {e}")
            return None