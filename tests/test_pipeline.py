"""
Tests Unitarios para el Pipeline
Valida la funcionalidad de cada módulo
"""

import pytest
import pandas as pd
import yaml
from datetime import datetime
from pathlib import Path
import sys

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from quality_tests import DataQualityTests


# Fixtures
@pytest.fixture
def config():
    """Carga la configuración de prueba"""
    config_path = Path(__file__).parent.parent / 'config' / 'pipeline_config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def sample_product_data():
    """Crea datos de productos de ejemplo para testing"""
    return pd.DataFrame({
        'product_id': [1, 2, 3, 4, 5],
        'title': ['Product A', 'Product B', 'Product C', 'Product D', 'Product E'],
        'price': [100.0, 50.0, 75.0, 200.0, 25.0],
        'category': ['electronics', 'jewelery', 'electronics', "men's clothing", 'jewelery'],
        'current_stock': [100, 50, 75, 200, 25],
        'min_stock': [50, 60, 40, 100, 30]
    })


@pytest.fixture
def sample_sales_data():
    """Crea datos de ventas de ejemplo"""
    return pd.DataFrame({
        'product_id': [1, 2, 3, 4, 5],
        'quantity_sold': [45, 32, 78, 23, 56],
        'sale_date': ['2024-10-15', '2024-10-16', '2024-10-17', '2024-10-18', '2024-10-19'],
        'customer_id': ['C001', 'C002', 'C003', 'C004', 'C005'],
        'sale_price': [109.95, 22.3, 55.99, 15.99, 695.0]
    })


# Tests de Calidad de Datos
class TestDataQuality:
    """Suite de tests para validaciones de calidad"""
    
    def test_no_negative_prices(self, config, sample_product_data):
        """Test 1: Verificar que no hay precios negativos"""
        quality_tests = DataQualityTests(config)
        passed, message = quality_tests.test_no_negative_prices(sample_product_data)
        
        assert passed == True
        assert "PASS" in message
        
    def test_no_negative_prices_fail(self, config):
        """Test 1: Verificar detección de precios negativos"""
        bad_data = pd.DataFrame({
            'product_id': [1, 2],
            'price': [100.0, -50.0]  # Precio negativo
        })
        
        quality_tests = DataQualityTests(config)
        passed, message = quality_tests.test_no_negative_prices(bad_data)
        
        assert passed == False
        assert "FAIL" in message
        
    def test_positive_integer_stock(self, config, sample_product_data):
        """Test 2: Validar stock positivo entero"""
        quality_tests = DataQualityTests(config)
        passed, message = quality_tests.test_positive_integer_stock(sample_product_data)
        
        assert passed == True
        assert "PASS" in message or "WARNING" in message
        
    def test_positive_integer_stock_fail(self, config):
        """Test 2: Detectar stock negativo"""
        bad_data = pd.DataFrame({
            'product_id': [1, 2],
            'current_stock': [100, -5]  # Stock negativo
        })
        
        quality_tests = DataQualityTests(config)
        passed, message = quality_tests.test_positive_integer_stock(bad_data)
        
        assert passed == False
        assert "FAIL" in message
        
    def test_valid_categories(self, config, sample_product_data):
        """Test 3: Validar categorías correctas"""
        quality_tests = DataQualityTests(config)
        passed, message = quality_tests.test_valid_categories(sample_product_data)
        
        assert passed == True
        assert "PASS" in message
        
    def test_valid_categories_fail(self, config):
        """Test 3: Detectar categorías inválidas"""
        bad_data = pd.DataFrame({
            'product_id': [1, 2],
            'category': ['electronics', 'invalid_category']  # Categoría inválida
        })
        
        quality_tests = DataQualityTests(config)
        passed, message = quality_tests.test_valid_categories(bad_data)
        
        assert passed == False
        assert "FAIL" in message
        
    def test_valid_sale_dates(self, config, sample_sales_data):
        """Test 4: Validar fechas de venta correctas"""
        quality_tests = DataQualityTests(config)
        passed, message = quality_tests.test_valid_sale_dates(sample_sales_data)
        
        assert passed == True
        assert "PASS" in message or "WARNING" in message
        
    def test_valid_sale_dates_fail(self, config):
        """Test 4: Detectar fechas inválidas"""
        bad_data = pd.DataFrame({
            'product_id': [1, 2],
            'sale_date': ['2024-10-15', 'invalid-date']  # Fecha inválida
        })
        
        quality_tests = DataQualityTests(config)
        passed, message = quality_tests.test_valid_sale_dates(bad_data)
        
        assert passed == False
        assert "FAIL" in message


# Tests de Configuración
class TestConfiguration:
    """Tests para validar configuración"""
    
    def test_config_loads_successfully(self, config):
        """Verificar que la configuración se carga correctamente"""
        assert config is not None
        assert 'pipeline' in config
        assert 'data_sources' in config
        assert 'storage' in config
        
    def test_config_has_required_fields(self, config):
        """Verificar campos requeridos en configuración"""
        assert 'api' in config['data_sources']
        assert 'csv_files' in config['data_sources']
        assert 'quality_tests' in config
        assert 'transformations' in config


# Tests de DataFrames
class TestDataFrames:
    """Tests para operaciones con DataFrames"""
    
    def test_sample_data_structure(self, sample_product_data):
        """Verificar estructura de datos de ejemplo"""
        assert len(sample_product_data) > 0
        assert 'product_id' in sample_product_data.columns
        assert 'price' in sample_product_data.columns
        assert 'category' in sample_product_data.columns
        
    def test_stock_calculation(self, sample_product_data):
        """Verificar cálculo de stock crítico"""
        critical = sample_product_data[
            sample_product_data['current_stock'] < sample_product_data['min_stock']
        ]
        
        # En los datos de ejemplo, product_id 2 y 5 tienen stock crítico
        assert len(critical) == 2
        assert 2 in critical['product_id'].values
        assert 5 in critical['product_id'].values


# Tests de Integración
class TestIntegration:
    """Tests de integración básicos"""
    
    def test_run_all_quality_tests(self, config, sample_product_data, sample_sales_data):
        """Ejecutar todos los tests de calidad"""
        # Crear DataFrame unificado simulado
        unified_df = sample_product_data.merge(
            sample_sales_data,
            on='product_id',
            how='left'
        )
        
        quality_tests = DataQualityTests(config)
        results = quality_tests.run_all_tests(unified_df)
        
        assert 'tests' in results
        assert 'summary' in results
        assert results['summary']['total'] == 4  # 4 tests configurados


if __name__ == '__main__':
    # Ejecutar tests
    pytest.main([__file__, '-v', '--tb=short'])