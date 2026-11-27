# SinoRadar Colombia v2.0 - Plataforma de Analisis de Mercado e Importaciones

Integrantes:
- Nicolas Alandete
- Santiago Plazas
- Isabella Prieto Morales
- Emmanuel Caballero

## Novedades v2.0 (despues de la presentacion de clase)
- Base de datos ampliada a **14,400 registros** (120 productos reales x 10 categorias x 24 meses x 5 ciudades).
- Carga de archivos CSV adicionales en modo **Combinar (`pd.concat`)** o **Reemplazar**.
- Pestana **Agregar Datos en Vivo** para registrar nuevas importaciones directamente desde la web.
- Descarga de plantilla CSV y descarga de la base maestra actualizada.
- Compatibilidad con **SKUs propios** en la plantilla CSV: acepta cualquier código interno de la empresa (ej. `EMP-001`) sin exigir prefijo `SR-`.

## Próximas mejoras (basadas en comentarios de clase)
- Lectura directa de archivos Excel (`.xlsx`) y generación automática de SKU con `pd.factorize` cuando el archivo no traiga esa columna.
- Cruce de productos externos contra la base de mercado usando código de barras (EAN/UPC) o partida arancelaria DIAN.
