"""
Módulo de Tests de Calidad de Datos
Implementa validaciones críticas sobre los datos
"""

import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Tuple


class DataQualityTests:
    """Clase para ejecutar tests de calidad sobre los datos"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.test_results = []
        
    def test_no_negative_prices(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Test 1: Verificar que no hay precios negativos
        
        Args:
            df: DataFrame a validar
            
        Returns:
            (passed, message)
        """
        test_name = "No Negative Prices"
        self.logger.info(f"Ejecutando test: {test_name}")
        
        try:
            if 'price' not in df.columns:
                return False, f"Columna 'price' no encontrada"
            
            negative_prices = df[df['price'] < 0]
            
            if len(negative_prices) == 0:
                message = f"✓ PASS: Todos los precios son positivos"
                self.logger.info(message)
                return True, message
            else:
                message = f"✗ FAIL: {len(negative_prices)} productos con precios negativos"
                self.logger.error(message)
                self.logger.error(f"Productos afectados: {negative_prices['product_id'].tolist()}")
                return False, message
                
        except Exception as e:
            message = f"✗ ERROR: {str(e)}"
            self.logger.error(message)
            return False, message
            
    def test_positive_integer_stock(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Test 2: Validar que stock sea número entero positivo
        
        Args:
            df: DataFrame a validar
            
        Returns:
            (passed, message)
        """
        test_name = "Positive Integer Stock"
        self.logger.info(f"Ejecutando test: {test_name}")
        
        try:
            if 'current_stock' not in df.columns:
                return False, f"Columna 'current_stock' no encontrada"
            
            # Verificar que sea numérico
            non_numeric = df[~df['current_stock'].apply(
                lambda x: pd.isna(x) or isinstance(x, (int, float))
            )]
            
            if len(non_numeric) > 0:
                message = f"✗ FAIL: {len(non_numeric)} registros con stock no numérico"
                self.logger.error(message)
                return False, message
            
            # Verificar que sea positivo
            negative_stock = df[df['current_stock'] < 0]
            
            if len(negative_stock) > 0:
                message = f"✗ FAIL: {len(negative_stock)} productos con stock negativo"
                self.logger.error(message)
                return False, message
            
            # Verificar que sea entero
            df_not_null = df[df['current_stock'].notna()]
            non_integer = df_not_null[df_not_null['current_stock'] % 1 != 0]
            
            if len(non_integer) > 0:
                message = f"⚠ WARNING: {len(non_integer)} productos con stock decimal"
                self.logger.warning(message)
                return True, message  # Warning, no falla
            
            message = f"✓ PASS: Todo el stock es entero positivo"
            self.logger.info(message)
            return True, message
            
        except Exception as e:
            message = f"✗ ERROR: {str(e)}"
            self.logger.error(message)
            return False, message
            
    def test_valid_categories(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Test 3: Confirmar que todas las categorías existen
        
        Args:
            df: DataFrame a validar
            
        Returns:
            (passed, message)
        """
        test_name = "Valid Categories"
        self.logger.info(f"Ejecutando test: {test_name}")
        
        try:
            if 'category' not in df.columns:
                return False, f"Columna 'category' no encontrada"
            
            valid_categories = self.config['transformations'].get('valid_categories', [])
            
            if not valid_categories:
                message = f"⚠ WARNING: No hay categorías configuradas para validar"
                self.logger.warning(message)
                return True, message
            
            # Obtener categorías únicas del dataset
            dataset_categories = df['category'].dropna().unique().tolist()
            
            # Encontrar categorías inválidas
            invalid_categories = [cat for cat in dataset_categories 
                                 if cat not in valid_categories]
            
            if len(invalid_categories) == 0:
                message = f"✓ PASS: Todas las categorías son válidas"
                self.logger.info(message)
                return True, message
            else:
                message = f"✗ FAIL: {len(invalid_categories)} categorías inválidas: {invalid_categories}"
                self.logger.error(message)
                return False, message
                
        except Exception as e:
            message = f"✗ ERROR: {str(e)}"
            self.logger.error(message)
            return False, message
            
    def test_valid_sale_dates(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Test 4: Verificar que fechas de venta sean válidas
        
        Args:
            df: DataFrame a validar
            
        Returns:
            (passed, message)
        """
        test_name = "Valid Sale Dates"
        self.logger.info(f"Ejecutando test: {test_name}")
        
        try:
            if 'sale_date' not in df.columns:
                return False, f"Columna 'sale_date' no encontrada"
            
            # Convertir a datetime
            df['sale_date_parsed'] = pd.to_datetime(df['sale_date'], errors='coerce')
            
            # Encontrar fechas inválidas (NaT después de conversión)
            invalid_dates = df[df['sale_date_parsed'].isna() & df['sale_date'].notna()]
            
            if len(invalid_dates) > 0:
                message = f"✗ FAIL: {len(invalid_dates)} fechas de venta inválidas"
                self.logger.error(message)
                return False, message
            
            # Verificar que las fechas no sean futuras
            today = datetime.now()
            future_dates = df[df['sale_date_parsed'] > today]
            
            if len(future_dates) > 0:
                message = f"✗ FAIL: {len(future_dates)} fechas de venta en el futuro"
                self.logger.error(message)
                return False, message
            
            # Verificar que las fechas no sean muy antiguas (> 10 años)
            min_date = pd.Timestamp('2015-01-01')
            old_dates = df[df['sale_date_parsed'] < min_date]
            
            if len(old_dates) > 0:
                message = f"⚠ WARNING: {len(old_dates)} fechas de venta muy antiguas (< 2015)"
                self.logger.warning(message)
                return True, message  # Warning, no falla
            
            message = f"✓ PASS: Todas las fechas de venta son válidas"
            self.logger.info(message)
            return True, message
            
        except Exception as e:
            message = f"✗ ERROR: {str(e)}"
            self.logger.error(message)
            return False, message
            
    def run_all_tests(self, unified_df: pd.DataFrame) -> Dict:
        """
        Ejecuta todos los tests de calidad configurados
        
        Args:
            unified_df: DataFrame unificado para validar
            
        Returns:
            Diccionario con resultados de los tests
        """
        self.logger.info("=" * 60)
        self.logger.info("INICIANDO TESTS DE CALIDAD DE DATOS")
        self.logger.info("=" * 60)
        
        quality_config = self.config.get('quality_tests', {})
        
        if not quality_config.get('enabled', True):
            self.logger.warning("Tests de calidad deshabilitados en configuración")
            return {'enabled': False}
        
        test_results = {
            'execution_time': datetime.now().isoformat(),
            'total_records': len(unified_df),
            'tests': []
        }
        
        # Test 1: No negative prices
        passed, message = self.test_no_negative_prices(unified_df)
        test_results['tests'].append({
            'name': 'no_negative_prices',
            'passed': passed,
            'message': message
        })
        
        # Test 2: Positive integer stock
        passed, message = self.test_positive_integer_stock(unified_df)
        test_results['tests'].append({
            'name': 'positive_integer_stock',
            'passed': passed,
            'message': message
        })
        
        # Test 3: Valid categories
        passed, message = self.test_valid_categories(unified_df)
        test_results['tests'].append({
            'name': 'valid_categories',
            'passed': passed,
            'message': message
        })
        
        # Test 4: Valid sale dates
        passed, message = self.test_valid_sale_dates(unified_df)
        test_results['tests'].append({
            'name': 'valid_sale_dates',
            'passed': passed,
            'message': message
        })
        
        # Resumen
        total_tests = len(test_results['tests'])
        passed_tests = sum(1 for t in test_results['tests'] if t['passed'])
        failed_tests = total_tests - passed_tests
        
        test_results['summary'] = {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': f"{(passed_tests/total_tests)*100:.1f}%"
        }
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("RESUMEN DE TESTS DE CALIDAD")
        self.logger.info("=" * 60)
        self.logger.info(f"Tests ejecutados: {total_tests}")
        self.logger.info(f"Tests exitosos: {passed_tests}")
        self.logger.info(f"Tests fallidos: {failed_tests}")
        self.logger.info(f"Tasa de éxito: {test_results['summary']['success_rate']}")
        
        # Verificar si debe fallar el pipeline
        if failed_tests > 0 and quality_config.get('fail_on_error', False):
            self.logger.error("Pipeline detenido por tests de calidad fallidos")
            test_results['pipeline_failed'] = True
        else:
            test_results['pipeline_failed'] = False
        
        return test_results