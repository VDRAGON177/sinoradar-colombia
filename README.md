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
- - **Manejo de SKUs externos:** Acepta los códigos SKU propios de cada empresa en la plantilla (sin necesidad de adivinarlos ni exigir `SR-`). Si un archivo viene sin SKU, se proyecta generarlos automáticamente con `pd.factorize`, y usar código de barras (EAN/UPC) o partida arancelaria para cruzar productos contra el mercado.
