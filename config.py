import os

# ── Directorio Base ───────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Rutas estáticas de recursos ───────────────────────────────────────────────
RUTA_IMG_MENU   = os.path.join(BASE_DIR, "assets", "menu.png")
RUTA_IMG_TALLER = os.path.join(BASE_DIR, "assets", "fondo de taller.png")
RUTA_IMG_LOGO   = os.path.join(BASE_DIR, "assets", "pixelgp.png")
RUTA_AUDIO_MENU = os.path.join(BASE_DIR, "assets", "song1.mp3")

# ── Diccionario Mapeo de Tilesets ─────────────────────────────────────────────
MAPA_TILESETS = {
    "dios santo.tsx": os.path.join(BASE_DIR, "assets", "RacecarTrack_WithoutRed.png"),
    "RacecarTrack_WithRed.tsx": os.path.join(BASE_DIR, "assets", "RacecarTrack_WithRed.png"),
    "Outside_Art-2.tsx": os.path.join(BASE_DIR, "assets", "Outside_Art-2.png"),
    "Outside_Art.tsx": os.path.join(BASE_DIR, "assets", "Outside_Art-2.png")
}

# ── Pantalla ──────────────────────────────────────────────────────────────────
ANCHO_JUEGO = 800      # Área de juego
PANEL_ANCHO = 220      # Panel lateral de posiciones
ANCHO = ANCHO_JUEGO + PANEL_ANCHO   # 1020
ALTO  = 608
FPS   = 60
ESCALA_MAPA = 9.0      # Factor de escalado de los recursos (alta resolución)

# ── Colores base ──────────────────────────────────────────────────────────────
NEGRO       = (0,   0,   0)
BLANCO      = (255, 255, 255)
ROJO        = (220,  55,  55)
AZUL        = ( 50, 120, 225)
VERDE       = ( 50, 200, 100)
AMARILLO    = (255, 210,  50)
GRIS        = (120, 125, 140)
GRIS_OSCURO = ( 28,  32,  48)
GRIS_CLARO  = (175, 182, 205)

# ── Colores UI premium ────────────────────────────────────────────────────────
COLOR_FONDO        = ( 10,  13,  22)
COLOR_PANEL        = ( 16,  20,  35)
COLOR_PANEL_BORDE  = ( 35,  45,  75)
COLOR_ACENTO       = (255, 185,   0)   # Dorado
COLOR_ACENTO2      = ( 90, 195, 255)   # Celeste
COLOR_ORO          = (255, 215,   0)
COLOR_PLATA        = (192, 195, 215)
COLOR_BRONCE       = (205, 127,  50)
COLOR_PISTA        = (220, 228, 255)

# ── Definición de carros ──────────────────────────────────────────────────────
# stat_veloc / stat_acel / stat_giro : valores de 1-10 para la barra visual
CARROS = [
    {
        "id": 0,
        "nombre": "VELOZ",
        "color": (220, 55, 55),
        "imagen": os.path.join(BASE_DIR, "assets", "carritos.png"),
        "audio": os.path.join(BASE_DIR, "assets", "carro 1.mp3"),
        "sprite_idx": 0,
        "descripcion": "Alta velocidad, giro moderado",
        "velocidad_maxima":   6.5,
        "aceleracion":        0.30,
        "velocidad_rotacion": 5.5,
        "stat_veloc": 9,
        "stat_acel":  5,
        "stat_giro":  6,
    },
    {
        "id": 1,
        "nombre": "POTENTE",
        "color": (50, 120, 225),
        "imagen": os.path.join(BASE_DIR, "assets", "carritos.png"),
        "audio": os.path.join(BASE_DIR, "assets", "carro 2.mp3"),
        "sprite_idx": 2,
        "descripcion": "Gran aceleración, vel. media",
        "velocidad_maxima":   5.5,
        "aceleracion":        0.45,
        "velocidad_rotacion": 6.0,
        "stat_veloc": 6,
        "stat_acel":  9,
        "stat_giro":  7,
    },
    {
        "id": 2,
        "nombre": "TECNICO",
        "color": (50, 200, 100),
        "imagen": os.path.join(BASE_DIR, "assets", "carritos.png"),
        "audio": os.path.join(BASE_DIR, "assets", "carro 1.mp3"),
        "sprite_idx": 4,
        "descripcion": "Giro excelente, vel. moderada",
        "velocidad_maxima":   5.0,
        "aceleracion":        0.35,
        "velocidad_rotacion": 8.0,
        "stat_veloc": 7,
        "stat_acel":  6,
        "stat_giro": 10,
    },
]

# ── Definición de mapas ───────────────────────────────────────────────────────
# checkpoints: (x, y, ancho, alto)  – en píxeles del mapa (800×608)
# Los checkpoints deben tocarse en orden para sumar vueltas.
MAPAS = [
    {
        "nombre":      "MAPA 1 SIIS",
        "archivo":     os.path.join(BASE_DIR, "mapa 2.json"),
        "descripcion": "Nuevo circuito optimizado (Tiled)",
        "checkpoints": [
            (740,  50, 40, 508),   
            ( 50, 558, 700, 40),   
            ( 30,  50, 40, 508),   
            ( 50,  20, 700, 40),   
        ],
        "pos_jugador":  (700, 290),
        "pos_enemigo":  (700, 345),
        "ruta_enemigo": [
            (750, 290), (750, 570), (400, 570),
            ( 50, 570), ( 50, 290), ( 50,  50),
            (400,  50), (750,  50),
        ],
        "angulo_jugador": 90,
        "vueltas": 3,
        "preview": os.path.join(BASE_DIR, "assets", "mapa 2.png"),
    },
    {
        "nombre":      "MAPA 2 SIIS",
        "archivo":     os.path.join(BASE_DIR, "mapa 1.json"),
        "descripcion": "Segundo circuito avanzado",
        "checkpoints": [
            (740,  50, 40, 508),   
            ( 50, 558, 700, 40),   
            ( 30,  50, 40, 508),   
            ( 50,  20, 700, 40),   
        ],
        "pos_jugador":  (700, 290),
        "pos_enemigo":  (700, 345),
        "ruta_enemigo": [
            (750, 290), (750, 570), (400, 570),
            ( 50, 570), ( 50, 290), ( 50,  50),
            (400,  50), (750,  50),
        ],
        "angulo_jugador": 90,
        "vueltas": 3,
        "preview": os.path.join(BASE_DIR, "assets", "mapa 1.png"),
    },
]
