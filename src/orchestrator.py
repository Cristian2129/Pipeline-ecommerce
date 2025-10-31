"""
Pipeline Principal de E-commerce
Orquesta el flujo completo de ingesta, transformación y calidad
"""

import yaml
import logging
from datetime import datetime
from pathlib import Path
import sys
import json

# Importar módulos del pipeline
from ingestion import DataIngestion
from transformation import DataTransformation
from quality_tests import DataQualityTests


class EcommerceDataPipeline:
    """Orquestador principal del pipeline de datos"""
    
    def __init__(self, config_path: str):
        """
        Inicializa el pipeline
        
        Args:
            config_path: Ruta al archivo de configuración YAML
        """
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.setup_directories()
        
        self.logger.info("Pipeline inicializado correctamente")
        
    def load_config(self, config_path: str) -> dict:
        """
        Carga la configuración desde archivo YAML
        
        Args:
            config_path: Ruta al archivo YAML
            
        Returns:
            Diccionario con configuración
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                print(f"✓ Configuración cargada desde: {config_path}")
                return config
        except FileNotFoundError:
            print(f"✗ Error: Archivo de configuración no encontrado: {config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"✗ Error al parsear YAML: {e}")
            sys.exit(1)
            
    def setup_logging(self):
        """Configura el sistema de logging"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('log_file', 'logs/pipeline_execution.log')
        log_format = log_config.get('format', 
                                     '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Crear directorio de logs si no existe
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Configurar logging
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, mode='a', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 80)
        self.logger.info(f"NUEVO PIPELINE INICIADO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 80)
        
    def setup_directories(self):
        """Crea los directorios necesarios para el pipeline"""
        directories = [
            'data/raw',
            'data/processed',
            'data/input',
            'logs',
            'reports'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
        self.logger.info("Directorios del pipeline verificados")
        
    def generate_report(self, execution_results: dict):
        """
        Genera un reporte de ejecución del pipeline
        
        Args:
            execution_results: Resultados de la ejecución
        """
        report_config = self.config.get('reporting', {})
        
        if not report_config.get('enabled', True):
            return
            
        report_path = report_config.get('output_path', 'reports/execution_report.txt')
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("REPORTE DE EJECUCIÓN DEL PIPELINE DE E-COMMERCE\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Fecha de ejecución: {execution_results['execution_time']}\n")
            f.write(f"Duración total: {execution_results['duration']:.2f} segundos\n")
            f.write(f"Estado: {execution_results['status']}\n\n")
            
            # Ingesta
            f.write("-" * 80 + "\n")
            f.write("1. INGESTA DE DATOS\n")
            f.write("-" * 80 + "\n")
            ingestion = execution_results.get('ingestion', {})
            f.write(f"Fuentes procesadas: {ingestion.get('sources_processed', 0)}/3\n")
            
            for source, count in ingestion.get('records', {}).items():
                f.write(f"  - {source}: {count} registros\n")
            f.write("\n")
            
            # Transformación
            f.write("-" * 80 + "\n")
            f.write("2. TRANSFORMACIÓN DE DATOS\n")
            f.write("-" * 80 + "\n")
            transformation = execution_results.get('transformation', {})
            f.write(f"Datasets generados: {transformation.get('datasets_generated', 0)}\n\n")
            
            # Métricas de negocio
            if 'metrics' in transformation:
                metrics = transformation['metrics']
                f.write("MÉTRICAS DE NEGOCIO:\n")
                f.write(f"  • Productos con stock crítico: {metrics.get('critical_stock_count', 0)}\n")
                f.write(f"  • Categorías analizadas: {metrics.get('categories_count', 0)}\n")
                f.write(f"  • Top productos identificados: {metrics.get('top_products_count', 0)}\n")
                f.write(f"  • Productos con análisis de rentabilidad: {metrics.get('profitability_count', 0)}\n\n")
            
            # Tests de calidad
            f.write("-" * 80 + "\n")
            f.write("3. TESTS DE CALIDAD\n")
            f.write("-" * 80 + "\n")
            quality = execution_results.get('quality_tests', {})
            
            if 'summary' in quality:
                summary = quality['summary']
                f.write(f"Tests ejecutados: {summary['total']}\n")
                f.write(f"Tests exitosos: {summary['passed']}\n")
                f.write(f"Tests fallidos: {summary['failed']}\n")
                f.write(f"Tasa de éxito: {summary['success_rate']}\n\n")
                
                f.write("RESULTADOS DETALLADOS:\n")
                for test in quality.get('tests', []):
                    status = "✓ PASS" if test['passed'] else "✗ FAIL"
                    f.write(f"  {status} - {test['name']}\n")
                    f.write(f"    {test['message']}\n")
                f.write("\n")
            
            # Errores
            if execution_results.get('errors'):
                f.write("-" * 80 + "\n")
                f.write("4. ERRORES ENCONTRADOS\n")
                f.write("-" * 80 + "\n")
                for error in execution_results['errors']:
                    f.write(f"  • {error}\n")
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write("FIN DEL REPORTE\n")
            f.write("=" * 80 + "\n")
            
        self.logger.info(f"✓ Reporte generado: {report_path}")
        
    def run_pipeline(self):
        """Ejecuta el pipeline completo"""
        start_time = datetime.now()
        execution_results = {
            'execution_time': start_time.isoformat(),
            'status': 'RUNNING',
            'errors': []
        }
        
        try:
            # FASE 1: INGESTA
            self.logger.info("\n" + "=" * 80)
            self.logger.info("FASE 1: INGESTA DE DATOS")
            self.logger.info("=" * 80)
            
            ingestion = DataIngestion(self.config)
            raw_data = ingestion.run_ingestion()
            
            if not raw_data:
                raise Exception("Ingesta falló: No se obtuvieron datos")
                
            execution_results['ingestion'] = {
                'sources_processed': len(raw_data),
                'records': {name: len(df) for name, df in raw_data.items()}
            }
            
            # FASE 2: TRANSFORMACIÓN
            self.logger.info("\n" + "=" * 80)
            self.logger.info("FASE 2: TRANSFORMACIÓN DE DATOS")
            self.logger.info("=" * 80)
            
            transformation = DataTransformation(self.config)
            transformed_data = transformation.run_transformations(raw_data)
            
            if not transformed_data:
                raise Exception("Transformación falló: No se generaron datos")
                
            execution_results['transformation'] = {
                'datasets_generated': len(transformed_data),
                'metrics': {
                    'critical_stock_count': len(transformed_data.get('critical_stock', [])),
                    'categories_count': len(transformed_data.get('sales_by_category', [])),
                    'top_products_count': len(transformed_data.get('top_products', [])),
                    'profitability_count': len(transformed_data.get('profitability', []))
                }
            }
            
            # FASE 3: TESTS DE CALIDAD
            self.logger.info("\n" + "=" * 80)
            self.logger.info("FASE 3: TESTS DE CALIDAD")
            self.logger.info("=" * 80)
            
            quality_tests = DataQualityTests(self.config)
            quality_results = quality_tests.run_all_tests(transformed_data['unified_data'])
            
            execution_results['quality_tests'] = quality_results
            
            # Verificar si el pipeline debe fallar
            if quality_results.get('pipeline_failed', False):
                execution_results['status'] = 'FAILED'
                raise Exception("Pipeline detenido por tests de calidad fallidos")
            
            # ÉXITO
            execution_results['status'] = 'SUCCESS'
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            execution_results['duration'] = duration
            
            self.logger.info("\n" + "=" * 80)
            self.logger.info("PIPELINE COMPLETADO EXITOSAMENTE")
            self.logger.info("=" * 80)
            self.logger.info(f"Duración total: {duration:.2f} segundos")
            
        except Exception as e:
            execution_results['status'] = 'FAILED'
            execution_results['errors'].append(str(e))
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            execution_results['duration'] = duration
            
            self.logger.error("\n" + "=" * 80)
            self.logger.error("PIPELINE FALLÓ")
            self.logger.error("=" * 80)
            self.logger.error(f"Error: {str(e)}")
            self.logger.error(f"Duración antes de fallar: {duration:.2f} segundos")
            
        finally:
            # Generar reporte siempre
            self.generate_report(execution_results)
            
            self.logger.info("\n" + "=" * 80)
            self.logger.info("FIN DE EJECUCIÓN DEL PIPELINE")
            self.logger.info("=" * 80 + "\n")
            
        return execution_results


if __name__ == "__main__":
    # Ejecutar pipeline
    pipeline = EcommerceDataPipeline('config/pipeline_config.yaml')
    results = pipeline.run_pipeline()
    
    # Salir con código de error si falló
    sys.exit(0 if results['status'] == 'SUCCESS' else 1)