"""
Módulo de Ingesta de Datos
Descarga datos de API REST y carga archivos CSV locales
"""

import requests
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import time


class DataIngestion:
    """Clase para manejar la ingesta de datos desde múltiples fuentes"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.ingestion_date = datetime.now().strftime('%Y-%m-%d')
        
    def fetch_api_data(self) -> Optional[pd.DataFrame]:
        """
        Descarga datos de productos desde Fake Store API
        
        Returns:
            DataFrame con productos o None si falla
        """
        api_config = self.config['data_sources']['api']
        base_url = api_config['base_url']
        endpoint = api_config['endpoints']['products']
        url = f"{base_url}{endpoint}"
        
        self.logger.info(f"Iniciando descarga desde API: {url}")
        
        max_retries = api_config.get('retry_attempts', 3)
        timeout = api_config.get('timeout', 30)
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                
                data = response.json()
                df = pd.DataFrame(data)
                
                # Agregar metadatos de ingesta
                df['ingestion_date'] = self.ingestion_date
                df['ingestion_timestamp'] = datetime.now()
                df['source'] = 'api'
                
                self.logger.info(f"✓ Descarga exitosa: {len(df)} productos obtenidos")
                return df
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Intento {attempt + 1}/{max_retries} falló: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error("No se pudo descargar datos de la API después de varios intentos")
                    return None
                    
    def load_csv_data(self, csv_type: str) -> Optional[pd.DataFrame]:
        """
        Carga datos desde archivo CSV local
        
        Args:
            csv_type: Tipo de CSV ('sales' o 'inventory')
            
        Returns:
            DataFrame con datos del CSV o None si falla
        """
        try:
            csv_config = self.config['data_sources']['csv_files'][csv_type]
            file_path = csv_config['path']
            encoding = csv_config.get('encoding', 'utf-8')
            separator = csv_config.get('separator', ',')
            
            self.logger.info(f"Cargando archivo CSV: {file_path}")
            
            # Verificar que el archivo existe
            if not Path(file_path).exists():
                self.logger.error(f"Archivo no encontrado: {file_path}")
                return None
            
            df = pd.read_csv(file_path, encoding=encoding, sep=separator)
            
            # Agregar metadatos de ingesta
            df['ingestion_date'] = self.ingestion_date
            df['ingestion_timestamp'] = datetime.now()
            df['source'] = f'csv_{csv_type}'
            
            self.logger.info(f"✓ CSV cargado exitosamente: {len(df)} registros")
            return df
            
        except Exception as e:
            self.logger.error(f"Error al cargar CSV {csv_type}: {str(e)}")
            return None
            
    def save_to_parquet(self, df: pd.DataFrame, filename: str) -> bool:
        """
        Guarda DataFrame en formato Parquet
        
        Args:
            df: DataFrame a guardar
            filename: Nombre del archivo
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        try:
            storage_config = self.config['storage']
            raw_path = storage_config['raw_data_path']
            compression = storage_config.get('compression', 'snappy')
            
            # Crear directorio si no existe
            output_dir = Path(raw_path) / self.ingestion_date
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / f"{filename}.parquet"
            
            self.logger.info(f"Guardando datos en: {output_file}")
            
            df.to_parquet(
                output_file,
                engine='pyarrow',
                compression=compression,
                index=False
            )
            
            file_size = output_file.stat().st_size / 1024  # KB
            self.logger.info(f"✓ Archivo guardado exitosamente: {file_size:.2f} KB")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al guardar Parquet: {str(e)}")
            return False
            
    def run_ingestion(self) -> Dict[str, pd.DataFrame]:
        """
        Ejecuta el proceso completo de ingesta
        
        Returns:
            Diccionario con DataFrames ingestados
        """
        self.logger.info("=" * 60)
        self.logger.info("INICIANDO PROCESO DE INGESTA")
        self.logger.info("=" * 60)
        
        results = {}
        
        # 1. Ingerir datos de API
        products_df = self.fetch_api_data()
        if products_df is not None:
            if self.save_to_parquet(products_df, 'products'):
                results['products'] = products_df
        
        # 2. Ingerir CSV de ventas
        sales_df = self.load_csv_data('sales')
        if sales_df is not None:
            if self.save_to_parquet(sales_df, 'sales'):
                results['sales'] = sales_df
        
        # 3. Ingerir CSV de inventario
        inventory_df = self.load_csv_data('inventory')
        if inventory_df is not None:
            if self.save_to_parquet(inventory_df, 'inventory'):
                results['inventory'] = inventory_df
        
        self.logger.info(f"\nIngesta completada: {len(results)}/3 fuentes procesadas")
        
        return results