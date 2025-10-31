# Parcial Segundo Corte 

## Estudiante: Cristian Vega
## Fecha: 31 de Octubre, 2025

---

## Ejercicio 1: Diseño de Pipeline (25 puntos)

### 1. Diagrama del Pipeline (10 puntos)

```
![Diagrama del Pipeline](pipeline_punto1.png)

```

**Componentes clave:**
- **Ingesta Streaming**: API REST con polling cada 5 minutos para productos nuevos
- **Ingesta Batch**: CSV procesados diariamente a las 00:00 AM
- **Storage**: Formato Parquet particionado por fecha
- **Procesamiento**: Python/Pandas con validaciones automáticas
- **Warehouse**: PostgreSQL para consultas analíticas

---

### 2. Justificación Técnica (15 puntos)

#### ¿Por qué diseñé así el pipeline?

**Arquitectura de medallones (Bronze-Silver-Gold):**
- **Bronze (Raw)**: Almacenamiento de datos crudos en Parquet, inmutables, con particionamiento temporal
- **Silver (Processed)**: Datos limpios y validados, con joins entre fuentes
- **Gold (Analytics)**: Métricas agregadas y modelos de negocio listos para consumo

**Razones del diseño:**
1. **Separación de responsabilidades**: Cada capa tiene un propósito específico
2. **Trazabilidad**: Los datos crudos se preservan para auditoría
3. **Reprocessamiento**: Posibilidad de reconstruir todo desde raw
4. **Performance**: Parquet ofrece compresión y lectura columnar eficiente
5. **Costo-efectividad**: Uso de herramientas open-source (sin cloud)

#### ¿Cómo garantiza la calidad de datos?

**Estrategia de Data Quality en 4 niveles:**

1. **Validaciones en Ingesta (Bronze → Silver)**:
   - Schema validation: Verificar tipos de datos esperados
   - Null checks: Identificar campos obligatorios faltantes
   - Range checks: Precios > 0, stock >= 0
   - Format validation: Fechas válidas, formatos de IDs

2. **Tests Unitarios**:
   ```python
   - test_no_negative_prices()
   - test_positive_integer_stock()
   - test_valid_categories()
   - test_valid_sale_dates()
   ```

3. **Reconciliación de Datos**:
   - Conteo de registros antes/después de transformaciones
   - Validación de integridad referencial entre tablas
   - Detección de duplicados por ID

4. **Monitoreo y Alertas**:
   - Logging detallado de cada paso
   - Métricas de pipeline: registros procesados, errores, tiempo
   - Alertas automáticas si falla validación crítica

#### ¿Qué estrategia usaría para los versionamientos?

**Estrategia de versionamiento multi-nivel:**

1. **Versionamiento de Código (Git)**:
   ```
   main → producción estable
   develop → integración de features
   feature/* → desarrollo de nuevas funcionalidades
   hotfix/* → correcciones urgentes
   ```

2. **Versionamiento de Datos**:
   - Particionamiento temporal: `/data/YYYY-MM-DD/`
   - Inmutabilidad de datos raw
   - Soft deletes en lugar de eliminar registros
   - Columnas de auditoría: `created_at`, `updated_at`, `version`

3. **Versionamiento de Schema**:
   - Migración con herramientas como Alembic
   - Backwards compatibility: mantener campos deprecados
   - Schema registry para documentar cambios
   - Semantic versioning: v1.0.0 → v1.1.0 → v2.0.0

4. **Versionamiento de Configuración**:
   - YAML versionados en Git
   - Environments separados: dev, staging, prod
   - Variables de entorno para secretos

#### ¿Cómo manejaría la escalabilidad?

**Estrategias de escalabilidad:**

1. **Escalabilidad Horizontal (corto plazo)**:
   - Particionamiento de datos por fecha y categoría
   - Procesamiento incremental (solo datos nuevos)
   - Paralelización con Python multiprocessing
   - Cache de resultados frecuentes

2. **Escalabilidad Vertical (mediano plazo)**:
   - Optimización de queries (índices, estadísticas)
   - Uso de DuckDB para análisis in-memory
   - Compresión de Parquet con codec Snappy/ZSTD
   - Lazy loading de datos

3. **Migración a Arquitectura Distribuida (largo plazo)**:
   ```
   Python/Pandas → PySpark/Dask
   PostgreSQL → ClickHouse/Apache Druid
   Batch → Streaming con Apache Kafka
   ```

4. **Optimizaciones específicas**:
   - Incremental loads: `WHERE created_at > last_run`
   - Aggregates pre-calculados para dashboards
   - Data retention policy: archivar datos > 2 años
   - Monitoring de recursos: CPU, memoria, I/O

