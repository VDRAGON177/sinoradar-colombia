"""
SinoRadar Colombia - Generador de Base de Datos Extensa (14,400 registros)
Autores: Isabella Prieto Morales, Santiago Plazas, Nicolás Alandete, Emmanuel Caballero

Construye una base de datos comercial reproducible y sustentable en Python (NumPy + Pandas):
  - 120 productos reales de importación China -> Colombia distribuidos en 10 categorías
  - 24 meses históricos (Enero 2025 - Diciembre 2026)
  - 5 ciudades principales de Colombia (Bogotá, Medellín, Cali, Barranquilla, Bucaramanga)
  - Identificadores universales determinísticos por producto: EAN_UPC (EAN-13 válido) y Partida_Arancelaria (DIAN)
  - Total: 14,400 registros x 24 columnas (0 valores nulos)
"""

import numpy as np
import pandas as pd

PARTIDAS_DIAN_POR_CATEGORIA = {
    "Tecnología": "8528.62.00.00",
    "Hogar Inteligente": "8509.80.20.00",
    "Belleza y Cuidado": "8543.70.90.00",
    "Deportes y Fitness": "9506.91.00.00",
    "Accesorios y Moda": "4202.92.00.00",
    "Mascotas y Eco": "3924.90.00.00",
    "Iluminación y Solar": "9405.42.00.00",
    "Cocina y Mini-Electro": "8509.40.10.00",
    "Gaming y Setup": "8471.60.20.00",
    "Bebés y Juguetería": "9503.00.99.00",
}


def calcular_ean13(indice_producto: int) -> str:
    """Genera un código de barras EAN-13 válido (prefijo GS1 China 690) determinístico."""
    base_12 = f"6901234{indice_producto:05d}"
    suma = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(base_12))
    digito_control = (10 - (suma % 10)) % 10
    return f"{base_12}{digito_control}"



def generar_base_datos(ruta_salida: str = "importaciones_china_colombia.csv", semilla: int = 42) -> pd.DataFrame:
    np.random.seed(semilla)

    # Formato por tupla:
    # (SKU, Producto, Categoria, FOB_USD, Arancel_Pct, Peso_Kg, Transporte,
    #  Demanda_Base_Bog, Comp_Base, Tendencia_Anual, Perfil, Rating_Base, Devolucion_Base)
    catalogo = [
        # ==================== 1. TECNOLOGÍA Y GADGETS (12) ====================
        ("SR-TEC-01", "Proyector Portátil Mini HD WiFi", "Tecnología", 23.5, 0.05, 0.85, "Aéreo", 210, 26, 0.28, "estrella", 4.7, 2.4),
        ("SR-TEC-02", "Audífonos Bluetooth ANC Pro", "Tecnología", 8.8, 0.05, 0.22, "Aéreo", 440, 74, 0.04, "competitivo", 4.3, 4.1),
        ("SR-TEC-03", "Smartwatch Deportivo AMOLED", "Tecnología", 12.0, 0.05, 0.18, "Aéreo", 390, 82, -0.08, "riesgo", 4.0, 6.5),
        ("SR-TEC-04", "Cargador Magnético Plegable 3 en 1", "Tecnología", 6.4, 0.05, 0.25, "Aéreo", 320, 34, 0.22, "estrella", 4.6, 2.8),
        ("SR-TEC-05", "Power Bank MagSafe 10000mAh Carga Rápida", "Tecnología", 9.2, 0.05, 0.28, "Aéreo", 350, 44, 0.19, "estrella", 4.6, 2.7),
        ("SR-TEC-06", "Mini Impresora Térmica Portátil Bluetooth", "Tecnología", 11.4, 0.05, 0.32, "Aéreo", 280, 30, 0.25, "estrella", 4.7, 2.3),
        ("SR-TEC-07", "Micrófono Inalámbrico Solapa USB-C Dual", "Tecnología", 7.1, 0.05, 0.16, "Aéreo", 310, 46, 0.16, "competitivo", 4.5, 3.1),
        ("SR-TEC-08", "Parlante Bluetooth Impermeable IPX7", "Tecnología", 10.5, 0.05, 0.58, "Marítimo", 370, 64, 0.03, "competitivo", 4.4, 3.8),
        ("SR-TEC-09", "Cámara de Seguridad WiFi 360° Doble Lente", "Tecnología", 14.2, 0.05, 0.45, "Aéreo", 330, 36, 0.24, "estrella", 4.6, 2.9),
        ("SR-TEC-10", "Localizador Inteligente GPS Compatible iOS/Android", "Tecnología", 3.8, 0.05, 0.08, "Aéreo", 410, 52, 0.15, "competitivo", 4.4, 3.3),
        ("SR-TEC-11", "Adaptador CarPlay / Android Auto Inalámbrico", "Tecnología", 13.0, 0.05, 0.14, "Aéreo", 220, 24, 0.31, "estrella", 4.7, 2.5),
        ("SR-TEC-12", "Anillo de Luz LED 10 Pulgadas con Trípode", "Tecnología", 4.5, 0.10, 0.72, "Marítimo", 360, 86, -0.14, "riesgo", 3.9, 5.7),

        # ==================== 2. HOGAR INTELIGENTE (12) ====================
        ("SR-HOG-01", "Mini Aspiradora Inalámbrica Auto/Hogar", "Hogar Inteligente", 8.2, 0.10, 0.65, "Marítimo", 330, 31, 0.24, "estrella", 4.6, 2.6),
        ("SR-HOG-02", "Humidificador Aromático Efecto Llama", "Hogar Inteligente", 4.9, 0.10, 0.45, "Marítimo", 370, 68, -0.05, "riesgo", 4.1, 5.2),
        ("SR-HOG-03", "Dispensador Automático de Jabón Sensor", "Hogar Inteligente", 4.4, 0.10, 0.40, "Marítimo", 250, 38, 0.12, "competitivo", 4.4, 3.5),
        ("SR-HOG-04", "Lámpara LED Escritorio Táctil Recargable", "Hogar Inteligente", 5.8, 0.10, 0.55, "Marítimo", 280, 49, 0.06, "competitivo", 4.4, 3.0),
        ("SR-HOG-05", "Cerradura Inteligente Huella Digital WiFi", "Hogar Inteligente", 26.0, 0.10, 1.35, "Marítimo", 165, 19, 0.34, "estrella", 4.8, 1.9),
        ("SR-HOG-06", "Enchufe Inteligente WiFi Medidor de Consumo", "Hogar Inteligente", 3.9, 0.10, 0.14, "Aéreo", 390, 42, 0.18, "competitivo", 4.5, 2.8),
        ("SR-HOG-07", "Robot Barredor Aspirador Compacto USB", "Hogar Inteligente", 18.5, 0.10, 1.45, "Marítimo", 210, 58, -0.09, "riesgo", 3.8, 6.8),
        ("SR-HOG-08", "Bomba Eléctrica Recargable para Botellón", "Hogar Inteligente", 2.4, 0.10, 0.30, "Marítimo", 490, 79, -0.07, "riesgo", 4.1, 4.9),
        ("SR-HOG-09", "Purificador de Aire HEPA Portátil USB", "Hogar Inteligente", 12.8, 0.10, 0.88, "Marítimo", 195, 22, 0.27, "estrella", 4.7, 2.2),
        ("SR-HOG-10", "Organizador Giratorio Nevera Acrílico", "Hogar Inteligente", 4.6, 0.15, 0.70, "Marítimo", 270, 35, 0.15, "competitivo", 4.5, 2.5),
        ("SR-HOG-11", "Plancha de Vapor Vertical Portátil Viaje", "Hogar Inteligente", 9.8, 0.10, 0.82, "Marítimo", 260, 41, 0.14, "competitivo", 4.4, 3.4),
        ("SR-HOG-12", "Timbre Inalámbrico con Cámara HD y App", "Hogar Inteligente", 15.6, 0.05, 0.36, "Aéreo", 205, 25, 0.29, "estrella", 4.6, 2.7),

        # ==================== 3. BELLEZA Y CUIDADO PERSONAL (12) ====================
        ("SR-BEL-01", "Masajeador Facial Microcorriente LED", "Belleza y Cuidado", 6.5, 0.15, 0.24, "Aéreo", 390, 29, 0.30, "estrella", 4.7, 2.5),
        ("SR-BEL-02", "Cepillo Secador Voluminizador 3 en 1", "Belleza y Cuidado", 9.6, 0.15, 0.68, "Marítimo", 360, 76, -0.06, "riesgo", 4.0, 5.8),
        ("SR-BEL-03", "Espejo Maquillaje LED Plegable USB", "Belleza y Cuidado", 4.1, 0.15, 0.42, "Marítimo", 310, 46, 0.10, "competitivo", 4.5, 3.3),
        ("SR-BEL-04", "Organizador Acrílico Giratorio 360°", "Belleza y Cuidado", 4.8, 0.15, 0.95, "Marítimo", 270, 62, -0.10, "riesgo", 4.1, 4.9),
        ("SR-BEL-05", "Depiladora Luz Pulsada IPL Portátil", "Belleza y Cuidado", 18.5, 0.15, 0.52, "Aéreo", 230, 27, 0.26, "estrella", 4.6, 3.1),
        ("SR-BEL-06", "Set Gua Sha + Rodillo Facial Cuarzo Natural", "Belleza y Cuidado", 2.9, 0.15, 0.28, "Marítimo", 430, 64, 0.04, "competitivo", 4.5, 2.9),
        ("SR-BEL-07", "Irrigador Bucal Portátil Recargable 4 Boquillas", "Belleza y Cuidado", 8.9, 0.10, 0.44, "Marítimo", 295, 28, 0.28, "estrella", 4.7, 2.4),
        ("SR-BEL-08", "Limpiador Facial Ultrasónico Silicona IPX7", "Belleza y Cuidado", 3.4, 0.15, 0.18, "Aéreo", 350, 71, -0.08, "riesgo", 4.1, 4.8),
        ("SR-BEL-09", "Rizador de Pestañas Térmico Recargable", "Belleza y Cuidado", 3.7, 0.15, 0.12, "Aéreo", 320, 33, 0.23, "estrella", 4.6, 2.7),
        ("SR-BEL-10", "Máquina Cortapelo Barbero Metálica Vintage", "Belleza y Cuidado", 5.6, 0.10, 0.36, "Marítimo", 440, 75, -0.05, "riesgo", 4.2, 4.6),
        ("SR-BEL-11", "Vaporizador Facial Nano Iónico Spa", "Belleza y Cuidado", 8.4, 0.15, 0.62, "Marítimo", 215, 36, 0.13, "competitivo", 4.4, 3.2),
        ("SR-BEL-12", "Mini Nevera Cosmética Skincare 4 Litros", "Belleza y Cuidado", 19.2, 0.15, 1.85, "Marítimo", 160, 21, 0.25, "estrella", 4.7, 2.6),

        # ==================== 4. DEPORTES Y FITNESS (12) ====================
        ("SR-DEP-01", "Pistola de Masaje Muscular Mini", "Deportes y Fitness", 13.8, 0.10, 0.62, "Marítimo", 290, 28, 0.25, "estrella", 4.7, 2.3),
        ("SR-DEP-02", "Botella Térmica Acero Inox 900ml Popote", "Deportes y Fitness", 4.3, 0.10, 0.48, "Marítimo", 480, 52, 0.14, "competitivo", 4.6, 1.8),
        ("SR-DEP-03", "Set Bandas de Resistencia Tela (3 pcs)", "Deportes y Fitness", 3.6, 0.15, 0.40, "Marítimo", 340, 79, -0.12, "riesgo", 4.2, 3.6),
        ("SR-DEP-04", "Cuerda de Saltar Inteligente Contador", "Deportes y Fitness", 5.2, 0.10, 0.30, "Aéreo", 210, 40, 0.08, "competitivo", 4.3, 3.4),
        ("SR-DEP-05", "Rodillo Abdominal con Rebote Automático", "Deportes y Fitness", 7.4, 0.10, 1.15, "Marítimo", 260, 33, 0.20, "estrella", 4.6, 2.7),
        ("SR-DEP-06", "Báscula Inteligente Bioimpedancia Bluetooth", "Deportes y Fitness", 7.9, 0.10, 1.30, "Marítimo", 285, 37, 0.21, "estrella", 4.6, 2.5),
        ("SR-DEP-07", "Colchoneta Yoga TPE Antideslizante 8mm", "Deportes y Fitness", 5.9, 0.15, 1.10, "Marítimo", 330, 61, 0.04, "competitivo", 4.4, 2.9),
        ("SR-DEP-08", "Straps y Muñequeras Gimnasio Acolchadas", "Deportes y Fitness", 2.6, 0.15, 0.22, "Marítimo", 380, 48, 0.15, "competitivo", 4.6, 1.9),
        ("SR-DEP-09", "Luz LED Recargable Bicicleta 1200 Lúmenes", "Deportes y Fitness", 4.8, 0.10, 0.24, "Aéreo", 315, 54, 0.07, "competitivo", 4.4, 3.2),
        ("SR-DEP-10", "Tabla de Flexiones Multifunción Plegable", "Deportes y Fitness", 5.4, 0.15, 1.25, "Marítimo", 275, 72, -0.11, "riesgo", 4.0, 4.7),
        ("SR-DEP-11", "Chaleco Hidratación Running Ultraligero", "Deportes y Fitness", 7.2, 0.15, 0.35, "Marítimo", 225, 24, 0.31, "estrella", 4.8, 2.0),
        ("SR-DEP-12", "Mini Bomba Eléctrica Portátil Llantas Bici/Auto", "Deportes y Fitness", 14.6, 0.10, 0.56, "Marítimo", 240, 26, 0.29, "estrella", 4.7, 2.4),

        # ==================== 5. ACCESORIOS Y MOVILIDAD (12) ====================
        ("SR-ACC-01", "Morral Antirrobo Impermeable Puerto USB", "Accesorios y Moda", 8.4, 0.15, 0.78, "Marítimo", 330, 58, 0.05, "competitivo", 4.4, 3.1),
        ("SR-ACC-02", "Gafas de Sol Polarizadas UV400", "Accesorios y Moda", 2.3, 0.15, 0.12, "Aéreo", 510, 88, -0.09, "riesgo", 3.9, 5.4),
        ("SR-ACC-03", "Soporte Magnético Celular Auto MagSafe", "Accesorios y Moda", 2.1, 0.10, 0.16, "Aéreo", 460, 72, -0.04, "riesgo", 4.1, 4.3),
        ("SR-ACC-04", "Organizador de Viaje Tech Impermeable", "Accesorios y Moda", 3.2, 0.15, 0.22, "Marítimo", 275, 24, 0.23, "estrella", 4.7, 2.0),
        ("SR-ACC-05", "Báscula Digital Portátil para Equipaje", "Accesorios y Moda", 2.8, 0.10, 0.15, "Aéreo", 240, 39, 0.11, "competitivo", 4.5, 2.6),
        ("SR-ACC-06", "Billetera Minimalista Aluminio Bloqueo RFID", "Accesorios y Moda", 3.1, 0.15, 0.11, "Aéreo", 390, 47, 0.16, "competitivo", 4.6, 2.3),
        ("SR-ACC-07", "Set 6 Cubos Organizadores Compresión Maleta", "Accesorios y Moda", 4.9, 0.15, 0.46, "Marítimo", 310, 27, 0.27, "estrella", 4.7, 1.9),
        ("SR-ACC-08", "Paraguas Plegable Automático Resistente Viento", "Accesorios y Moda", 3.8, 0.15, 0.42, "Marítimo", 420, 55, 0.09, "competitivo", 4.4, 3.2),
        ("SR-ACC-09", "Maleta Cabina Mochila Expandible Avión", "Accesorios y Moda", 14.5, 0.15, 1.15, "Marítimo", 250, 26, 0.30, "estrella", 4.8, 2.1),
        ("SR-ACC-10", "Correa Silicona Deportiva Smartwatch Pack 3", "Accesorios y Moda", 1.7, 0.15, 0.09, "Aéreo", 540, 91, -0.13, "riesgo", 3.9, 5.1),
        ("SR-ACC-11", "Almohada Cervical Viaje Memory Foam Plegable", "Accesorios y Moda", 4.2, 0.15, 0.38, "Marítimo", 280, 41, 0.12, "competitivo", 4.5, 2.4),
        ("SR-ACC-12", "Bolso Pechero Cruzado Impermeable Urbano", "Accesorios y Moda", 5.3, 0.15, 0.36, "Marítimo", 335, 34, 0.21, "estrella", 4.6, 2.5),

        # ==================== 6. MASCOTAS Y ECO-HOGAR (12) ====================
        ("SR-MAS-01", "Fuente de Agua Automática Mascotas Filtro", "Mascotas y Eco", 7.6, 0.10, 0.74, "Marítimo", 310, 25, 0.32, "estrella", 4.8, 2.1),
        ("SR-MAS-02", "Cepillo Vaporizador Mascotas Autolimpiante", "Mascotas y Eco", 3.4, 0.10, 0.26, "Aéreo", 380, 30, 0.29, "estrella", 4.6, 2.5),
        ("SR-MAS-03", "Bolsas Biodegradables Mascotas (Pack 12)", "Mascotas y Eco", 2.5, 0.10, 0.50, "Marítimo", 420, 55, 0.12, "competitivo", 4.5, 1.7),
        ("SR-MAS-04", "Tapete Olfativo Interactivo Perros", "Mascotas y Eco", 4.6, 0.15, 0.45, "Marítimo", 220, 44, 0.09, "competitivo", 4.4, 2.8),
        ("SR-MAS-05", "Collar LED Recargable Nocturno Mascotas", "Mascotas y Eco", 1.9, 0.15, 0.10, "Aéreo", 290, 75, -0.11, "riesgo", 3.9, 5.9),
        ("SR-MAS-06", "Comedero Automático Programable WiFi 4L", "Mascotas y Eco", 22.0, 0.10, 1.65, "Marítimo", 175, 20, 0.35, "estrella", 4.8, 2.2),
        ("SR-MAS-07", "Botella Bebedero Portátil Perros con Filtro", "Mascotas y Eco", 2.7, 0.15, 0.24, "Marítimo", 360, 58, 0.06, "competitivo", 4.4, 3.0),
        ("SR-MAS-08", "Morral Burbuja Transparente Transporte Gatos", "Mascotas y Eco", 8.9, 0.15, 1.18, "Marítimo", 240, 49, 0.08, "competitivo", 4.5, 3.3),
        ("SR-MAS-09", "Rodillo Quita Pelos Reutilizable Sofá/Ropa", "Mascotas y Eco", 2.2, 0.15, 0.22, "Marítimo", 460, 67, -0.04, "riesgo", 4.2, 3.9),
        ("SR-MAS-10", "Cama Antiestrés Felpa Lavable Mascotas", "Mascotas y Eco", 6.8, 0.15, 1.05, "Marítimo", 310, 52, 0.11, "competitivo", 4.5, 2.7),
        ("SR-MAS-11", "Juguete Pelota Inteligente Rodante Recargable", "Mascotas y Eco", 3.9, 0.15, 0.16, "Aéreo", 295, 29, 0.24, "estrella", 4.6, 2.8),
        ("SR-MAS-12", "Cortauñas Mascotas con Luz LED y Lupa", "Mascotas y Eco", 2.6, 0.10, 0.15, "Aéreo", 265, 35, 0.17, "competitivo", 4.5, 2.3),

        # ==================== 7. ILUMINACIÓN Y ENERGÍA SOLAR (12) ====================
        ("SR-ILU-01", "Reflector Solar Exterior 200W Control Remoto", "Iluminación y Solar", 9.8, 0.10, 1.40, "Marítimo", 340, 46, 0.18, "competitivo", 4.5, 3.0),
        ("SR-ILU-02", "Panel Solar Plegable Portátil 30W USB-C", "Iluminación y Solar", 17.5, 0.05, 0.92, "Marítimo", 165, 18, 0.33, "estrella", 4.7, 2.1),
        ("SR-ILU-03", "Tira LED Neón Flexible RGB 5m App WiFi", "Iluminación y Solar", 5.2, 0.10, 0.48, "Marítimo", 410, 65, 0.03, "competitivo", 4.3, 4.0),
        ("SR-ILU-04", "Lámpara Sensor Movimiento Clóset Recargable", "Iluminación y Solar", 2.6, 0.10, 0.18, "Aéreo", 450, 36, 0.24, "estrella", 4.7, 2.2),
        ("SR-ILU-05", "Proyector Galaxia Astronauta con Temporizador", "Iluminación y Solar", 6.2, 0.10, 0.42, "Marítimo", 390, 74, -0.07, "riesgo", 4.1, 4.8),
        ("SR-ILU-06", "Guirnalda Luces Solares Jardín Vintage 15m", "Iluminación y Solar", 6.9, 0.10, 0.85, "Marítimo", 290, 40, 0.16, "competitivo", 4.6, 2.6),
        ("SR-ILU-07", "Bombillo Inteligente WiFi RGBW Pack 4", "Iluminación y Solar", 7.4, 0.10, 0.36, "Aéreo", 330, 56, 0.07, "competitivo", 4.4, 3.3),
        ("SR-ILU-08", "Estación Energía Portátil Mini 150Wh Camping", "Iluminación y Solar", 42.0, 0.05, 1.95, "Marítimo", 115, 15, 0.36, "estrella", 4.8, 1.8),
        ("SR-ILU-09", "Linterna Táctica LED Zoom Recargable USB-C", "Iluminación y Solar", 3.5, 0.10, 0.25, "Marítimo", 380, 69, -0.06, "riesgo", 4.2, 4.2),
        ("SR-ILU-10", "Lámpara Mesa Inalámbrica Aluminio Restaurante", "Iluminación y Solar", 6.8, 0.10, 0.62, "Marítimo", 260, 27, 0.29, "estrella", 4.7, 2.3),
        ("SR-ILU-11", "Aplique Solar Pared Exterior Doble Haz (Pack 2)", "Iluminación y Solar", 4.9, 0.10, 0.54, "Marítimo", 320, 44, 0.14, "competitivo", 4.5, 2.9),
        ("SR-ILU-12", "Barra de Luz Monitor LED Antirreflejo USB", "Iluminación y Solar", 8.6, 0.10, 0.48, "Marítimo", 230, 23, 0.27, "estrella", 4.7, 2.0),

        # ==================== 8. COCINA Y ELECTRODOMÉSTICOS MINI (12) ====================
        ("SR-COC-01", "Licuadora Portátil Recargable 6 Cuchillas USB-C", "Cocina y Mini-Electro", 5.8, 0.10, 0.56, "Marítimo", 430, 73, -0.06, "riesgo", 4.1, 5.3),
        ("SR-COC-02", "Selladora al Vacío Alimentos con Bolsas", "Cocina y Mini-Electro", 9.4, 0.10, 0.92, "Marítimo", 265, 32, 0.22, "estrella", 4.6, 2.7),
        ("SR-COC-03", "Báscula Gramera Digital Acero Inox 5kg", "Cocina y Mini-Electro", 2.9, 0.10, 0.28, "Marítimo", 440, 62, 0.05, "competitivo", 4.5, 2.8),
        ("SR-COC-04", "Espumador de Leche Recargable Doble Batidor", "Cocina y Mini-Electro", 3.6, 0.10, 0.22, "Aéreo", 370, 38, 0.19, "estrella", 4.6, 2.4),
        ("SR-COC-05", "Mini Procesador Ajos Eléctrico Recargable", "Cocina y Mini-Electro", 3.1, 0.10, 0.34, "Marítimo", 410, 77, -0.09, "riesgo", 4.0, 5.0),
        ("SR-COC-06", "Dispensador Aceite Spray Vidrio 2 en 1", "Cocina y Mini-Electro", 2.4, 0.15, 0.36, "Marítimo", 470, 33, 0.26, "estrella", 4.7, 2.1),
        ("SR-COC-07", "Cafetera Espresso Portátil 3 en 1 Viaje", "Cocina y Mini-Electro", 19.5, 0.10, 0.78, "Aéreo", 185, 19, 0.34, "estrella", 4.8, 2.2),
        ("SR-COC-08", "Termómetro Digital Carne Lectura Instantánea", "Cocina y Mini-Electro", 2.7, 0.10, 0.12, "Aéreo", 290, 41, 0.13, "competitivo", 4.6, 2.0),
        ("SR-COC-09", "Afilador de Cuchillos 4 Etapas Profesional", "Cocina y Mini-Electro", 2.5, 0.15, 0.26, "Marítimo", 350, 58, 0.04, "competitivo", 4.3, 3.1),
        ("SR-COC-10", "Lonchera Eléctrica Calentadora Auto/Oficina", "Cocina y Mini-Electro", 7.8, 0.10, 0.85, "Marítimo", 295, 35, 0.21, "estrella", 4.6, 2.8),
        ("SR-COC-11", "Set Tapetes Silicona Reutilizable Air Fryer (x2)", "Cocina y Mini-Electro", 2.3, 0.15, 0.32, "Marítimo", 490, 68, -0.03, "competitivo", 4.4, 2.6),
        ("SR-COC-12", "Molinillo Eléctrico Sal y Pimienta Gravedad", "Cocina y Mini-Electro", 4.7, 0.10, 0.42, "Marítimo", 260, 29, 0.23, "estrella", 4.6, 2.5),

        # ==================== 9. GAMING Y OFICINA / SETUP (12) ====================
        ("SR-GAM-01", "Teclado Mecánico Compacto 65% Hot-Swap RGB", "Gaming y Setup", 15.5, 0.05, 0.72, "Marítimo", 290, 36, 0.22, "estrella", 4.7, 2.6),
        ("SR-GAM-02", "Mouse Gamer Inalámbrico Ultraligero 2.4G", "Gaming y Setup", 9.8, 0.05, 0.18, "Aéreo", 340, 42, 0.20, "estrella", 4.6, 2.9),
        ("SR-GAM-03", "Base Refrigerante Laptop 6 Ventiladores RGB", "Gaming y Setup", 6.8, 0.05, 0.88, "Marítimo", 310, 66, -0.06, "riesgo", 4.1, 4.4),
        ("SR-GAM-04", "Brazo Articulado Hidráulico para Monitor", "Gaming y Setup", 12.4, 0.10, 2.35, "Marítimo", 245, 29, 0.26, "estrella", 4.7, 2.1),
        ("SR-GAM-05", "Hub USB-C 8 en 1 HDMI 4K + Ethernet 1Gbps", "Gaming y Setup", 8.2, 0.05, 0.15, "Aéreo", 320, 38, 0.19, "estrella", 4.6, 2.7),
        ("SR-GAM-06", "Desk Mat Escritorio Cuero Vegano Impermeable", "Gaming y Setup", 3.4, 0.15, 0.45, "Marítimo", 410, 52, 0.11, "competitivo", 4.5, 2.2),
        ("SR-GAM-07", "Soporte Aluminio Plegable Ergonómico Laptop", "Gaming y Setup", 4.2, 0.10, 0.32, "Marítimo", 460, 76, -0.08, "riesgo", 4.3, 3.5),
        ("SR-GAM-08", "Diadema Gamer Inalámbrica Baja Latencia", "Gaming y Setup", 14.0, 0.05, 0.48, "Marítimo", 275, 51, 0.09, "competitivo", 4.4, 3.8),
        ("SR-GAM-09", "Soporte Vertical Doble Laptop Aluminio", "Gaming y Setup", 5.9, 0.10, 0.64, "Marítimo", 210, 24, 0.24, "estrella", 4.7, 1.9),
        ("SR-GAM-10", "Webcam Full HD 1080p con Tapa Privacidad", "Gaming y Setup", 6.5, 0.05, 0.22, "Aéreo", 265, 71, -0.13, "riesgo", 4.0, 4.9),
        ("SR-GAM-11", "Kit Limpieza 7 en 1 Pantallas y Teclados", "Gaming y Setup", 1.8, 0.15, 0.12, "Aéreo", 440, 59, 0.07, "competitivo", 4.4, 2.5),
        ("SR-GAM-12", "Control Inalámbrico Multiplataforma Hall Effect", "Gaming y Setup", 13.2, 0.05, 0.34, "Aéreo", 260, 27, 0.29, "estrella", 4.7, 2.6),

        # ==================== 10. BEBÉS Y JUGUETERÍA EDUCATIVA (12) ====================
        ("SR-BEB-01", "Monitor Bebé Cámara WiFi Visión Nocturna", "Bebés y Juguetería", 16.5, 0.05, 0.42, "Aéreo", 215, 26, 0.25, "estrella", 4.7, 2.5),
        ("SR-BEB-02", "Bloques Magnéticos Construcción 64 Piezas", "Bebés y Juguetería", 7.8, 0.15, 0.95, "Marítimo", 310, 31, 0.28, "estrella", 4.8, 1.9),
        ("SR-BEB-03", "Tablero Sensorial Montessori Fieltro Viaje", "Bebés y Juguetería", 4.5, 0.15, 0.38, "Marítimo", 295, 34, 0.23, "estrella", 4.7, 2.1),
        ("SR-BEB-04", "Extractor de Leche Eléctrico Manos Libres", "Bebés y Juguetería", 13.5, 0.10, 0.46, "Aéreo", 240, 25, 0.31, "estrella", 4.7, 2.8),
        ("SR-BEB-05", "Tableta Dibujo LCD Borrable 10 Pulgadas", "Bebés y Juguetería", 2.4, 0.15, 0.20, "Marítimo", 480, 84, -0.10, "riesgo", 4.0, 5.1),
        ("SR-BEB-06", "Set Vajilla Silicona Bebé Antideslizante 6 pcs", "Bebés y Juguetería", 4.8, 0.15, 0.44, "Marítimo", 335, 45, 0.14, "competitivo", 4.6, 2.2),
        ("SR-BEB-07", "Cámara Digital Infantil Impresión Instantánea", "Bebés y Juguetería", 11.2, 0.10, 0.32, "Aéreo", 270, 29, 0.27, "estrella", 4.6, 2.9),
        ("SR-BEB-08", "Pañalera Morral Impermeable con Cambiador", "Bebés y Juguetería", 9.4, 0.15, 0.92, "Marítimo", 290, 53, 0.08, "competitivo", 4.5, 2.7),
        ("SR-BEB-09", "Pistola Burbujas Eléctrica Recargable LED", "Bebés y Juguetería", 3.1, 0.15, 0.36, "Marítimo", 420, 78, -0.08, "riesgo", 3.9, 5.8),
        ("SR-BEB-10", "Calentador Biberones Portátil USB-C", "Bebés y Juguetería", 6.2, 0.10, 0.28, "Aéreo", 250, 33, 0.21, "estrella", 4.6, 2.6),
        ("SR-BEB-11", "Microscopio Portátil Educativo LED 120x Niños", "Bebés y Juguetería", 3.9, 0.10, 0.22, "Aéreo", 285, 37, 0.18, "competitivo", 4.5, 2.5),
        ("SR-BEB-12", "Mini Dron Sensor Obstáculos Recargable Niños", "Bebés y Juguetería", 8.6, 0.15, 0.34, "Aéreo", 300, 69, -0.09, "riesgo", 3.9, 6.2),
    ]

    ciudades = {
        "Bogotá":       {"factor_dem": 1.00, "puerto_mar": "Buenaventura", "ajuste_precio": 1.00},
        "Medellín":     {"factor_dem": 0.65, "puerto_mar": "Cartagena",    "ajuste_precio": 1.02},
        "Cali":         {"factor_dem": 0.45, "puerto_mar": "Buenaventura", "ajuste_precio": 0.97},
        "Barranquilla": {"factor_dem": 0.37, "puerto_mar": "Cartagena",    "ajuste_precio": 0.98},
        "Bucaramanga":  {"factor_dem": 0.26, "puerto_mar": "Cartagena",    "ajuste_precio": 0.99},
    }

    # Estacionalidad comercial en Colombia (1 = Enero ... 12 = Diciembre)
    estacionalidad = np.array([
        0.74, 0.79, 0.88, 0.94, 1.26, 1.16,
        0.96, 1.01, 1.06, 1.12, 1.42, 1.68
    ])

    # Fechas: 24 meses (Enero 2025 - Diciembre 2026)
    fechas = pd.date_range(start="2025-01-01", periods=24, freq="MS")

    # Simulación realista de TRM mensual (COP/USD)
    trm_serie = np.zeros(24)
    trm_serie[0] = 4180.0
    for i in range(1, 24):
        trm_serie[i] = np.clip(trm_serie[i - 1] + np.random.normal(8, 65), 3920.0, 4480.0)
    trm_serie = np.round(trm_serie, 2)

    iva_pct = 0.19
    gastos_nac_pct = 0.08

    registros = []

    for idx_t, fecha in enumerate(fechas):
        anio = fecha.year
        mes = fecha.month
        trm_mes = trm_serie[idx_t]
        factor_est = estacionalidad[mes - 1]
        progreso_anual = idx_t / 12.0

        for idx_prod, (sku, prod, cat, fob, arancel, peso, transp,
             dem_base, comp_base, tend_anual, perfil, rating_base, dev_base) in enumerate(catalogo, start=1):
            ean_upc = calcular_ean13(idx_prod)
            partida_dian = PARTIDAS_DIAN_POR_CATEGORIA.get(cat, "8543.70.90.00")

            if transp == "Marítimo":
                flete_usd = round(max(0.45, peso * np.random.uniform(1.15, 1.55)), 2)
                transito_dias = int(np.random.randint(40, 54))
            else:
                flete_usd = round(max(1.20, peso * np.random.uniform(6.2, 8.0)), 2)
                transito_dias = int(np.random.randint(8, 15))

            cif_usd = fob + flete_usd
            arancel_usd = cif_usd * arancel
            iva_usd = (cif_usd + arancel_usd) * iva_pct
            gastos_loc_usd = cif_usd * gastos_nac_pct
            costo_aterrizado_cop = int(np.round(((cif_usd + arancel_usd + iva_usd + gastos_loc_usd) * trm_mes) / 100.0) * 100)

            if perfil == "estrella":
                mult_precio = np.random.uniform(2.15, 2.65)
                ratio_import_vs_venta = np.random.uniform(1.03, 1.14)
            elif perfil == "competitivo":
                mult_precio = np.random.uniform(1.68, 2.08)
                ratio_import_vs_venta = np.random.uniform(1.12, 1.28)
            else:
                mult_precio = np.random.uniform(1.30, 1.58)
                ratio_import_vs_venta = np.random.uniform(1.32, 1.68)

            factor_tendencia = max(0.45, 1.0 + tend_anual * progreso_anual)

            for ciudad, cfg in ciudades.items():
                puerto = "Aéreo El Dorado" if transp == "Aéreo" else cfg["puerto_mar"]

                precio_venta_cop = int(
                    np.round((costo_aterrizado_cop * mult_precio * cfg["ajuste_precio"]) / 500.0) * 500
                )

                media_demanda = dem_base * cfg["factor_dem"] * factor_est * factor_tendencia
                unidades_vendidas = int(max(10, np.random.normal(media_demanda, media_demanda * 0.12)))
                unidades_importadas = int(max(unidades_vendidas, np.round(unidades_vendidas * ratio_import_vs_venta)))

                comp_ciudad = comp_base * (0.55 + 0.45 * cfg["factor_dem"])
                deriva_comp = 1.0 + (0.08 if perfil == "riesgo" else 0.02) * progreso_anual
                competidores = int(max(4, np.round(comp_ciudad * deriva_comp + np.random.randint(-3, 5))))

                rating = float(np.round(np.clip(rating_base + np.random.normal(0, 0.12), 3.2, 5.0), 2))
                devolucion_pct = float(np.round(np.clip(dev_base + np.random.normal(0, 0.45), 0.5, 12.0), 2))

                registros.append({
                    "Fecha": fecha.strftime("%Y-%m-%d"),
                    "Anio": anio,
                    "Mes": mes,
                    "SKU": sku,
                    "EAN_UPC": ean_upc,
                    "Partida_Arancelaria": partida_dian,
                    "Producto": prod,
                    "Categoria": cat,
                    "Ciudad_Destino": ciudad,
                    "Tipo_Transporte": transp,
                    "Puerto_Entrada": puerto,
                    "Tiempo_Transito_Dias": transito_dias,
                    "TRM_COP": trm_mes,
                    "Precio_FOB_USD": fob,
                    "Flete_Unitario_USD": flete_usd,
                    "Arancel_Pct": arancel,
                    "IVA_Pct": iva_pct,
                    "Costo_Aterrizado_COP": costo_aterrizado_cop,
                    "Precio_Venta_Mercado_COP": precio_venta_cop,
                    "Unidades_Importadas": unidades_importadas,
                    "Unidades_Vendidas": unidades_vendidas,
                    "Competidores_Activos": competidores,
                    "Calificacion_Mercado": rating,
                    "Tasa_Devolucion_Pct": devolucion_pct,
                })

    df = pd.DataFrame(registros)
    df.to_csv(ruta_salida, index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    df_generado = generar_base_datos()
    print(f"Base de datos generada exitosamente: {df_generado.shape[0]:,} filas x {df_generado.shape[1]} columnas.")
    print(f"SKUs únicos: {df_generado['SKU'].nunique()} | Categorías: {df_generado['Categoria'].nunique()} | Ciudades: {df_generado['Ciudad_Destino'].nunique()}")
