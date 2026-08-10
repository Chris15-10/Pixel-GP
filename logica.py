import pygame
import math
import json
import os
from pygame.math import Vector2
from config import *


CAR_IMAGE_CACHE = {}

def cargar_imagen_carro(ruta_imagen, ancho_deseado=48, sprite_idx=0):
    if (ruta_imagen, ancho_deseado, sprite_idx) in CAR_IMAGE_CACHE:
        return CAR_IMAGE_CACHE[(ruta_imagen, ancho_deseado, sprite_idx)]
    
    try:
        raw = pygame.image.load(ruta_imagen).convert_alpha()
        w_total = raw.get_width()
        if w_total > 50: 
            cw = w_total // 5
            raw = raw.subsurface(pygame.Rect(sprite_idx * cw, 0, cw, raw.get_height()))

        rect = raw.get_bounding_rect()
        cropped = raw.subsurface(rect)
        rot = pygame.transform.rotate(cropped, -90)
        w, h = rot.get_size()
        target_h = max(1, int(ancho_deseado * (h / w)))
        scaled = pygame.transform.smoothscale(rot, (ancho_deseado, target_h))
        CAR_IMAGE_CACHE[(ruta_imagen, ancho_deseado, sprite_idx)] = scaled
        return scaled
    except Exception as e:
        print(f"[AVISO] No se pudo cargar la imagen {ruta_imagen}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
class Vehiculo(pygame.sprite.Sprite):
    """Clase base para todos los vehículos del juego."""

    def __init__(self, x, y, color, stats=None):
        super().__init__()

        img_cargada = None
        
        escala = globals().get('ESCALA_MAPA', 1.0)
        t_largo = int(8 * escala)
        t_ancho = max(1, t_largo // 2)

        if stats and "imagen" in stats:
            idx = stats.get("sprite_idx", 0)
            img_cargada = cargar_imagen_carro(stats["imagen"], ancho_deseado=t_largo, sprite_idx=idx)

        if img_cargada:
            self.imagen_original = img_cargada
        else:
            raise FileNotFoundError("La imagen del carro no pudo cargarse desde los assets.")

        self.image = self.imagen_original
        self.rect  = self.image.get_rect(center=(x, y))
        self.mask  = pygame.mask.from_surface(self.image)

        self.posicion       = Vector2(x, y)
        self.posicion_segura = Vector2(x, y)
        self.velocidad_vector = Vector2(0, 0)

        self.angulo        = 0
        self.angulo_seguro = 0
        self.velocidad     = 0
        self.acelerando    = False
        self.frenando      = False
        self.girando       = False
        
        self.dir_movimiento = Vector2(1, 0)

        if stats:
            self.velocidad_maxima   = stats.get("velocidad_maxima",   6.0)
            self.aceleracion        = stats.get("aceleracion",         0.2)
            self.velocidad_rotacion = stats.get("velocidad_rotacion",  4.0)
        else:
            self.velocidad_maxima   = 6.0
            self.aceleracion        = 0.2
            self.velocidad_rotacion = 4.0

        self.friccion_base = 0.05
        self.friccion      = self.friccion_base

        self.checkpoint_actual = 0

    # ── Física ────────────────────────────────────────────────────────────────

    def aplicar_friccion(self, tipo_terreno="ASFALTO"):
        if tipo_terreno != "PARED":
            self.posicion_segura = Vector2(self.posicion)
            self.angulo_seguro   = self.angulo

        if tipo_terreno == "PASTO":
            self.friccion = 0.15
            vel_max = self.velocidad_maxima * 0.5
        elif tipo_terreno == "PARED":
            self.posicion = Vector2(self.posicion_segura)
            self.angulo   = self.angulo_seguro
            self.velocidad = -(self.velocidad * 0.5)
            if abs(self.velocidad) < 1:
                self.velocidad = -1
            self.friccion = self.friccion_base
            vel_max = self.velocidad_maxima
        else:
            self.friccion = self.friccion_base
            vel_max = self.velocidad_maxima

        friccion = 0.35
        if not self.acelerando and not self.frenando:
            if self.velocidad > friccion:
                self.velocidad -= friccion
            elif self.velocidad < -friccion:
                self.velocidad += friccion
            else:
                self.velocidad = 0
        else:
            if self.velocidad > 0:
                self.velocidad -= self.friccion
                if self.velocidad < 0:
                    self.velocidad = 0
            elif self.velocidad < 0:
                self.velocidad += self.friccion
                if self.velocidad > 0:
                    self.velocidad = 0

        self.velocidad = max(-vel_max / 2, min(self.velocidad, vel_max))

    def actualizar_fisicas(self):
        rad = math.radians(self.angulo)
        dir_carro = Vector2(math.cos(rad), -math.sin(rad))
        
        # ── Sistema de Drift ──
        speed = abs(self.velocidad)
        if speed > 0.5 and self.girando and not self.frenando:
            drift_factor = 0.18
        else:
            drift_factor = 0.55

        self.dir_movimiento = self.dir_movimiento.lerp(dir_carro, drift_factor)
        if self.dir_movimiento.length() > 0:
            self.dir_movimiento = self.dir_movimiento.normalize()
        
        self.velocidad_vector = self.dir_movimiento * self.velocidad
        self.posicion += self.velocidad_vector

    def rotar_imagen(self):
        self.image = pygame.transform.rotate(self.imagen_original, self.angulo)
        self.rect  = self.image.get_rect(center=(round(self.posicion.x), round(self.posicion.y)))
        self.mask  = pygame.mask.from_surface(self.image)


# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
class Jugador(Vehiculo):
    """Vehículo controlado por el jugador con teclado."""

    def __init__(self, x, y, stats=None, sonido_motor=None):
        color = stats["color"] if stats and "color" in stats else ROJO
        super().__init__(x, y, color, stats)
        self.acelerando = False
        self.frenando   = False
        self.girando    = False
        self.sonido_motor = sonido_motor
        self.sonido_reproduciendo = False

    def procesar_entradas(self, teclas):
        self.acelerando = False
        self.frenando   = False
        self.girando    = False
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            if abs(self.velocidad) > 0.3:
                self.angulo += self.velocidad_rotacion
            self.girando = True
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            if abs(self.velocidad) > 0.3:
                self.angulo -= self.velocidad_rotacion
            self.girando = True
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            self.velocidad += self.aceleracion
            self.acelerando = True
        elif teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            self.velocidad -= self.aceleracion * 1.5
            self.frenando = True
            
        if self.sonido_motor:
            if self.acelerando and not self.sonido_reproduciendo:
                self.sonido_motor.play(-1)
                self.sonido_reproduciendo = True
            elif not self.acelerando and self.sonido_reproduciendo:
                self.sonido_motor.stop()
                self.sonido_reproduciendo = False

    def update(self, tipo_terreno="ASFALTO"):
        teclas = pygame.key.get_pressed()
        self.procesar_entradas(teclas)
        self.aplicar_friccion(tipo_terreno)
        self.actualizar_fisicas()
        self.rotar_imagen()


# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
class Enemigo(Vehiculo):
    """Vehículo controlado por IA con pathfinding básico y rubber-banding."""

    def __init__(self, x, y, puntos_ruta, stats=None, jugador_referencia=None):
        color = stats["color"] if stats and "color" in stats else AZUL
        super().__init__(x, y, color, stats)
        self.puntos_ruta        = puntos_ruta
        self.indice_punto_actual = 0
        self.jugador_referencia = jugador_referencia
        self.vel_max_base       = self.velocidad_maxima

    def calcular_ia(self):
        if not self.puntos_ruta:
            return

        objetivo = self.puntos_ruta[self.indice_punto_actual]
        dx = objetivo[0] - self.posicion.x
        dy = objetivo[1] - self.posicion.y
        distancia = math.hypot(dx, dy)

        if distancia < 150:
            self.indice_punto_actual = (self.indice_punto_actual + 1) % len(self.puntos_ruta)
            objetivo = self.puntos_ruta[self.indice_punto_actual]
            dx = objetivo[0] - self.posicion.x
            dy = objetivo[1] - self.posicion.y

        angulo_obj = math.degrees(math.atan2(-dy, dx))
        diferencia = (angulo_obj - self.angulo) % 360
        if diferencia > 180:
            diferencia -= 360

        if abs(diferencia) < self.velocidad_rotacion:
            self.angulo = angulo_obj
        elif diferencia > 0:
            self.angulo += self.velocidad_rotacion
        else:
            self.angulo -= self.velocidad_rotacion

        if self.jugador_referencia:
            dist_jug = self.posicion.distance_to(self.jugador_referencia.posicion)
            if dist_jug > 220:
                self.velocidad_maxima = self.vel_max_base * 1.12
            elif dist_jug < 90:
                self.velocidad_maxima = self.vel_max_base * 0.88
            else:
                self.velocidad_maxima = self.vel_max_base

        self.velocidad += self.aceleracion
        self.acelerando = True
        self.frenando   = False

    def update(self, tipo_terreno="ASFALTO"):
        self.calcular_ia()
        self.aplicar_friccion(tipo_terreno)
        self.actualizar_fisicas()
        self.rotar_imagen()


# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
class Circuito:
    """Carga y gestiona el mapa de tiles desde un archivo JSON."""

    def __init__(self):
        self.mascara_paredes = None
        self.mascara_pasto   = None
        self.fondo           = None
        self.ancho_px        = ANCHO_JUEGO
        self.alto_px         = ALTO

    def cargar_desde_json(self, ruta):
        with open(ruta, "r") as f:
            datos = json.load(f)

        escala = globals().get('ESCALA_MAPA', 1.0)
        ancho_mapa  = datos.get("width", 25)
        alto_mapa   = datos.get("height", 19)
        ancho_tile_orig = datos.get("tilewidth", 32)
        alto_tile_orig  = datos.get("tileheight", 32)
        
        ancho_tile = int(ancho_tile_orig * escala)
        alto_tile  = int(alto_tile_orig * escala)

        self.ancho_px = ancho_mapa * ancho_tile
        self.alto_px  = alto_mapa  * alto_tile

        self.fondo = pygame.Surface((self.ancho_px, self.alto_px))
        self.fondo.fill((50, 52, 55))

        # ── Cargar tilesets ──
        tilesets = []
        for ts in datos.get("tilesets", []):
            firstgid = ts["firstgid"]
            source = ts.get("source", ts.get("image", ""))
            
            nombre_base = os.path.basename(source)
            if nombre_base in MAPA_TILESETS:
                img_path = MAPA_TILESETS[nombre_base]
            else:
                nombre_archivo = nombre_base.replace(".tsx", ".png")
                img_path = os.path.join(BASE_DIR, "assets", nombre_archivo)

            try:
                img = pygame.image.load(img_path).convert_alpha()
            except FileNotFoundError:
                print(f"[AVISO] No se pudo cargar el tileset: {img_path}")
                continue

            cols = img.get_width() // ancho_tile_orig
            rows = img.get_height() // alto_tile_orig
            tile_count = cols * rows
            tilesets.append({
                "firstgid": firstgid,
                "image": img,
                "cols": cols,
                "lastgid": firstgid + tile_count - 1
            })

        tilesets.sort(key=lambda x: x["firstgid"], reverse=True)

        surf_paredes = pygame.Surface((self.ancho_px, self.alto_px), pygame.SRCALPHA)
        surf_pasto   = pygame.Surface((self.ancho_px, self.alto_px), pygame.SRCALPHA)

        for capa in datos.get("layers", []):
            if capa["type"] != "tilelayer":
                continue
            nombre = capa["name"]
            arreglo = capa["data"]

            for idx, id_tile in enumerate(arreglo):
                flip_h = bool(id_tile & 0x80000000)
                flip_v = bool(id_tile & 0x40000000)
                flip_d = bool(id_tile & 0x20000000)
                
                id_real = id_tile & 0x0FFFFFFF
                
                if id_real > 0:
                    x = (idx % ancho_mapa) * ancho_tile
                    y = (idx // ancho_mapa) * alto_tile
                    r = (x, y, ancho_tile, alto_tile)

                    for ts in tilesets:
                        if ts["firstgid"] <= id_real <= ts["lastgid"]:
                            local_id = id_real - ts["firstgid"]
                            tx = (local_id % ts["cols"]) * ancho_tile_orig
                            ty = (local_id // ts["cols"]) * alto_tile_orig
                            t_rect = pygame.Rect(tx, ty, ancho_tile_orig, alto_tile_orig)
                            
                            try:
                                tile_img = ts["image"].subsurface(t_rect)
                                
                                if flip_d:
                                    tile_img = pygame.transform.rotate(tile_img, -90)
                                    tile_img = pygame.transform.flip(tile_img, False, True)
                                if flip_h or flip_v:
                                    tile_img = pygame.transform.flip(tile_img, flip_h, flip_v)
                                
                                if nombre == "cesped":
                                    t_w = int(ancho_tile_orig * 1.5)
                                    t_h = int(alto_tile_orig * 1.5)
                                    tile_img = pygame.transform.scale(tile_img, (t_w, t_h))
                                    self.fondo.blit(tile_img, (x, y))
                                else:
                                    if escala != 1.0:
                                        tile_img = pygame.transform.scale(tile_img, (ancho_tile, alto_tile))
                                    self.fondo.blit(tile_img, (x, y))
                            except ValueError:
                                pass
                            break

                    if nombre == "Pasto":
                        pygame.draw.rect(surf_pasto, (255, 255, 255), r)
                    elif nombre == "Paredes":
                        pygame.draw.rect(surf_paredes, (255, 255, 255), r)

        self._decorar_fondo()

        self.mascara_pasto   = pygame.mask.from_surface(surf_pasto)
        self.mascara_paredes = pygame.mask.from_surface(surf_paredes)

        # ── Extraer ruta y punto de salida ──
        self.puntos_ruta_ia = []
        puntos_desordenados = []
        self.punto_salida = None
        
        for capa in datos.get("layers", []):
            if capa["type"] == "objectgroup" and capa["name"] == "RutaIA":
                for obj in capa.get("objects", []):
                    if "polyline" in obj:
                        bx, by = obj["x"], obj["y"]
                        for pt in obj["polyline"]:
                            self.puntos_ruta_ia.append((bx + pt["x"], by + pt["y"]))
                    elif "point" in obj and obj["point"]:
                        self.puntos_ruta_ia.append((obj["x"], obj["y"]))
            
            elif capa["type"] == "tilelayer" and capa["name"] == "IA":
                arreglo = capa["data"]
                for idx, id_tile in enumerate(arreglo):
                    if id_tile > 0:
                        x = (idx % ancho_mapa) * ancho_tile + ancho_tile // 2
                        y = (idx // ancho_mapa) * alto_tile + alto_tile // 2
                        puntos_desordenados.append((x, y))

            elif capa["type"] == "tilelayer" and capa["name"] == "Capa de patrones 2":
                arreglo = capa["data"]
                for idx, id_tile in enumerate(arreglo):
                    if id_tile > 0:
                        x = (idx % ancho_mapa) * ancho_tile + ancho_tile // 2
                        y = (idx // ancho_mapa) * alto_tile + alto_tile // 2
                        self.punto_salida = (x, y)
                        break

        if puntos_desordenados:
            if self.punto_salida:
                actual = min(puntos_desordenados, key=lambda p: math.hypot(p[0]-self.punto_salida[0], p[1]-self.punto_salida[1]))
                puntos_desordenados.remove(actual)
            else:
                actual = puntos_desordenados.pop(0)
                
            self.puntos_ruta_ia.append(actual)
            while puntos_desordenados:
                mas_cercano = min(puntos_desordenados, key=lambda p: math.hypot(p[0]-actual[0], p[1]-actual[1]))
                self.puntos_ruta_ia.append(mas_cercano)
                puntos_desordenados.remove(mas_cercano)
                actual = mas_cercano

    def _decorar_fondo(self):
        """Añade líneas de carril y detalles visuales al fondo ya generado."""
        if self.fondo is None:
            return

    def comprobar_colision(self, mascara_vehiculo, offset):
        if self.mascara_paredes and self.mascara_paredes.overlap(mascara_vehiculo, offset):
            return "PARED"
        if self.mascara_pasto and self.mascara_pasto.overlap(mascara_vehiculo, offset):
            return "PASTO"
        return "ASFALTO"


# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
class Camara:
    """Desplaza la vista siguiendo al jugador dentro de los límites del mapa."""

    def __init__(self, ancho, alto):
        self.rect_camara = pygame.Rect(0, 0, ancho, alto)
        self.ancho = ancho
        self.alto  = alto

    def aplicar(self, entidad):
        return entidad.rect.move(self.rect_camara.topleft)

    def aplicar_rect(self, rect):
        return rect.move(self.rect_camara.topleft)

    def actualizar(self, objetivo, ancho_px_mapa, alto_px_mapa):
        x = -objetivo.rect.centerx + self.ancho // 2
        y = -objetivo.rect.centery + self.alto  // 2

        x = min(0, x)
        y = min(0, y)

        if ancho_px_mapa > self.ancho:
            x = max(-(ancho_px_mapa - self.ancho), x)
        if alto_px_mapa > self.alto:
            y = max(-(alto_px_mapa  - self.alto),  y)

        self.rect_camara = pygame.Rect(x, y, self.ancho, self.alto)
