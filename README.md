# SinoRadar Colombia v2.0 - Plataforma de Analisis de Mercado e Importaciones

Integrantes:
- Isabella Prieto Morales
- Santiago Plazas
- Nicolas Alandete
- Emmanuel Caballero

## Novedades v2.0
- Base de datos ampliada a **14,400 registros** (120 productos reales x 10 categorias x 24 meses x 5 ciudades).
- Carga de archivos CSV adicionales en modo **Combinar (`pd.concat`)** o **Reemplazar**.
- Pestana **Agregar Datos en Vivo** para registrar nuevas importaciones directamente desde la web.
- Descarga de plantilla CSV y descarga de la base maestra actualizada.

## Archivos incluidos
1. `app.py` - Aplicacion web interactiva (Streamlit + Pandas + NumPy + Plotly).
2. `importaciones_china_colombia.csv` - Base de datos de 14,400 registros (2.6 MB).
3. `generar_datos.py` - Script reproducible en Python (NumPy + Pandas) para regenerar o escalar los datos.
4. `requirements.txt` - Dependencias exactas para Render o ejecucion local.

## Como desplegar en Render (via GitHub)
1. Descomprime el ZIP y sube los 5 archivos a tu repositorio en GitHub.
2. En Render -> New + -> Web Service -> conecta tu repositorio.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
