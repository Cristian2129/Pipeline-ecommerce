"""
Módulo de Transformación de Datos
Realiza joins, cálculos de métricas y agregaciones
"""

import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple


class DataTransformation:
    """Clase para transformaciones y cálculos de métricas de negocio"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.ingestion_date = datetime.now().strftime('%Y-%m-%d')
        
    def join_datasets(self, products: pd.DataFrame, sales: pd.DataFrame, 
                     inventory: pd.DataFrame) -> pd.DataFrame:
        """
        Une los tres datasets en un único DataFrame
        
        Args:
            products: DataFrame de productos de la API
            sales: DataFrame de ventas
            inventory: DataFrame de inventario
            
        Returns:
            DataFrame unificado
        """
        self.logger.info("Uniendo datasets...")
        
        # Renombrar columna 'id' en products para evitar conflictos
        products_clean = products.rename(columns={'id': 'product_id'})
        
        # Join productos con ventas (left join para mantener todos los productos)
        merged = products_clean.merge(
            sales,
            on='product_id',
            how='left',
            suffixes=('', '_sale')
        )
        
        # Join con inventario
        merged = merged.merge(
            inventory,
            on='product_id',
            how='left',
            suffixes=('', '_inv')
        )
        
        self.logger.info(f"✓ Datasets unidos: {len(merged)} registros totales")
        
        return merged
        
    def calculate_critical_stock(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identifica productos con stock crítico
        
        Args:
            df: DataFrame unificado
            
        Returns:
            DataFrame con productos en stock crítico
        """
        self.logger.info("Calculando productos con stock crítico...")
        
        threshold = self.config['transformations'].get('stock_critical_threshold', 10)
        
        # Filtrar productos donde stock actual < stock mínimo
        critical = df[
            (df['current_stock'].notna()) & 
            (df['min_stock'].notna()) &
            (df['current_stock'] < df['min_stock'])
        ].copy()
        
        critical['stock_deficit'] = critical['min_stock'] - critical['current_stock']
        critical['criticality_level'] = pd.cut(
            critical['stock_deficit'],
            bins=[0, 5, 10, float('inf')],
            labels=['Low', 'Medium', 'High']
        )
        
        # Ordenar por déficit descendente
        critical = critical.sort_values('stock_deficit', ascending=False)
        
        self.logger.info(f"✓ {len(critical)} productos con stock crítico identificados")
        
        return critical[['product_id', 'title', 'category', 'current_stock', 
                        'min_stock', 'stock_deficit', 'criticality_level']]
        
    def calculate_sales_by_category(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula ventas totales por categoría
        
        Args:
            df: DataFrame unificado
            
        Returns:
            DataFrame con ventas por categoría
        """
        self.logger.info("Calculando ventas por categoría...")
        
        # Calcular ingresos totales por cada venta
        df['total_revenue'] = df['price'] * df['quantity_sold']
        
        # Agrupar por categoría
        sales_by_category = df.groupby('category').agg({
            'quantity_sold': 'sum',
            'total_revenue': 'sum',
            'product_id': 'nunique'  # Número de productos únicos
        }).reset_index()
        
        sales_by_category.columns = ['category', 'total_units_sold', 
                                     'total_revenue', 'unique_products']
        
        # Calcular ticket promedio
        sales_by_category['avg_price_per_unit'] = (
            sales_by_category['total_revenue'] / sales_by_category['total_units_sold']
        )
        
        # Ordenar por ingresos
        sales_by_category = sales_by_category.sort_values('total_revenue', ascending=False)
        
        self.logger.info(f"✓ Ventas calculadas para {len(sales_by_category)} categorías")
        
        return sales_by_category
        
    def calculate_top_products(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identifica los productos más vendidos
        
        Args:
            df: DataFrame unificado
            
        Returns:
            DataFrame con top productos
        """
        self.logger.info("Calculando productos más vendidos...")
        
        limit = self.config['transformations'].get('top_products_limit', 10)
        
        # Agrupar por producto
        product_sales = df.groupby(['product_id', 'title', 'category']).agg({
            'quantity_sold': 'sum',
            'price': 'first',
            'rating': lambda x: x.dropna().apply(lambda r: r.get('rate', 0) if isinstance(r, dict) else 0).mean()
        }).reset_index()
        
        # Calcular revenue total
        product_sales['total_revenue'] = product_sales['price'] * product_sales['quantity_sold']
        
        # Ordenar y tomar top N
        top_products = product_sales.nlargest(limit, 'quantity_sold')
        
        # Agregar ranking
        top_products['rank'] = range(1, len(top_products) + 1)
        
        self.logger.info(f"✓ Top {len(top_products)} productos identificados")
        
        return top_products[['rank', 'product_id', 'title', 'category', 
                            'quantity_sold', 'total_revenue', 'rating']]
        
    def calculate_profitability(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula rentabilidad por producto
        
        Args:
            df: DataFrame unificado
            
        Returns:
            DataFrame con análisis de rentabilidad
        """
        self.logger.info("Calculando rentabilidad por producto...")
        
        # Asumiendo que el costo es 60% del precio de venta (dato ficticio)
        df['estimated_cost'] = df['price'] * 0.6
        df['profit_per_unit'] = df['price'] - df['estimated_cost']
        df['total_profit'] = df['profit_per_unit'] * df['quantity_sold']
        df['profit_margin'] = (df['profit_per_unit'] / df['price']) * 100
        
        # Agrupar por producto
        profitability = df.groupby(['product_id', 'title', 'category']).agg({
            'quantity_sold': 'sum',
            'total_profit': 'sum',
            'profit_margin': 'mean',
            'price': 'first'
        }).reset_index()
        
        # Clasificar rentabilidad
        profitability['profitability_class'] = pd.cut(
            profitability['profit_margin'],
            bins=[0, 30, 40, 100],
            labels=['Low', 'Medium', 'High']
        )
        
        # Ordenar por profit total
        profitability = profitability.sort_values('total_profit', ascending=False)
        
        self.logger.info(f"✓ Rentabilidad calculada para {len(profitability)} productos")
        
        return profitability
        
    def save_transformed_data(self, dataframes: Dict[str, pd.DataFrame]) -> bool:
        """
        Guarda los DataFrames transformados en Parquet
        
        Args:
            dataframes: Diccionario con DataFrames a guardar
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            storage_config = self.config['storage']
            processed_path = storage_config['processed_data_path']
            compression = storage_config.get('compression', 'snappy')
            
            # Crear directorio si no existe
            output_dir = Path(processed_path) / self.ingestion_date
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for name, df in dataframes.items():
                output_file = output_dir / f"{name}.parquet"
                
                self.logger.info(f"Guardando {name}: {output_file}")
                
                df.to_parquet(
                    output_file,
                    engine='pyarrow',
                    compression=compression,
                    index=False
                )
                
            self.logger.info(f"✓ {len(dataframes)} datasets transformados guardados")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al guardar datos transformados: {str(e)}")
            return False
            
    def run_transformations(self, raw_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Ejecuta todas las transformaciones
        
        Args:
            raw_data: Diccionario con DataFrames crudos
            
        Returns:
            Diccionario con DataFrames transformados
        """
        self.logger.info("=" * 60)
        self.logger.info("INICIANDO PROCESO DE TRANSFORMACIÓN")
        self.logger.info("=" * 60)
        
        results = {}
        
        try:
            # 1. Join de datasets
            unified_df = self.join_datasets(
                raw_data['products'],
                raw_data['sales'],
                raw_data['inventory']
            )
            results['unified_data'] = unified_df
            
            # 2. Stock crítico
            critical_stock = self.calculate_critical_stock(unified_df)
            results['critical_stock'] = critical_stock
            
            # 3. Ventas por categoría
            sales_by_category = self.calculate_sales_by_category(unified_df)
            results['sales_by_category'] = sales_by_category
            
            # 4. Top productos
            top_products = self.calculate_top_products(unified_df)
            results['top_products'] = top_products
            
            # 5. Rentabilidad
            profitability = self.calculate_profitability(unified_df)
            results['profitability'] = profitability
            
            # Guardar datos transformados
            self.save_transformed_data(results)
            
            self.logger.info(f"\nTransformación completada: {len(results)} datasets generados")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error en transformaciones: {str(e)}")
            return {}