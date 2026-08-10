"""
Top-Down Racing Arcade – main.py
Máquina de estados:
  MENU → SELECCION_CARRO → SELECCION_MAPA → JUGANDO → VICTORIA / DERROTA → MENU
"""

import pygame
import sys
import math
import os
from pygame.math import Vector2
from config import *
from logica import Jugador, Enemigo, Circuito, Camara, cargar_imagen_carro


class GestorJuego:

    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Top-Down Racing Arcade  ·  POO")
        self.reloj = pygame.time.Clock()

        self.f_titulo = pygame.font.SysFont("Arial", 60, bold=True)
        self.f_grande = pygame.font.SysFont("Arial", 38, bold=True)
        self.f_media  = pygame.font.SysFont("Arial", 28, bold=True)
        self.f_normal = pygame.font.SysFont("Arial", 22)
        self.f_hud    = pygame.font.SysFont("Arial", 20, bold=True)
        self.f_mini   = pygame.font.SysFont("Arial", 16)

        self.estado      = "MENU"
        self.carro_idx   = 0
        self.mapa_idx    = 0
        self.tiempo_anim = 0

        self.grupo_sprites    = pygame.sprite.Group()
        self.circuito         = None
        self.jugador          = None
        self.enemigo          = None
        self.camara           = None
        self.checkpoints      = []
        self.vueltas_para_ganar = 3
        self.vueltas_jugador  = 0
        self.vueltas_enemigo  = 0
        self.tiempo_inicio    = 0
        self.tiempo_fin       = 0
        self.enemigo_car      = None
        self.tiempo_conteo    = 0
        self.t_ultima_vuelta  = 0

        pygame.mixer.init()
        try:
            pygame.mixer.music.load(RUTA_AUDIO_MENU)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"[AVISO] No se pudo cargar música del menú: {e}")

        self.bg_menu   = pygame.transform.scale(pygame.image.load(RUTA_IMG_MENU).convert(), (ANCHO, ALTO))
        self.bg_taller = pygame.transform.scale(pygame.image.load(RUTA_IMG_TALLER).convert(), (ANCHO, ALTO))
        
        logo_original = pygame.image.load(RUTA_IMG_LOGO).convert_alpha()
        ancho_deseado = 600
        ratio = ancho_deseado / logo_original.get_width()
        nuevo_alto = int(logo_original.get_height() * ratio)
        
        self.img_logo = pygame.transform.smoothscale(logo_original, (ancho_deseado, nuevo_alto))

        self.map_previews = []
        for m in MAPAS:
            ruta = m.get("preview")
            if ruta and os.path.exists(ruta):
                try:
                    img = pygame.image.load(ruta).convert_alpha()
                    img = pygame.transform.smoothscale(img, (324, 168))
                    self.map_previews.append(img)
                except Exception as e:
                    print(f"[AVISO] Error cargando preview {ruta}: {e}")
                    self.map_previews.append(None)
            else:
                self.map_previews.append(None)


    # ── Inicio de partida ────────────────────────────────────────────────────

    def iniciar_partida(self):
        mapa  = MAPAS[self.mapa_idx]
        carro = CARROS[self.carro_idx]

        self.vueltas_para_ganar = mapa["vueltas"]
        self.vueltas_jugador    = 0
        self.vueltas_enemigo    = 0
        self.grupo_sprites      = pygame.sprite.Group()

        self.circuito = Circuito()
        try:
            self.circuito.cargar_desde_json(mapa["archivo"])
        except FileNotFoundError:
            print(f"[AVISO] {mapa['archivo']} no encontrado. Sin pista visual.")

        if hasattr(self.circuito, "punto_salida") and self.circuito.punto_salida:
            px, py = self.circuito.punto_salida
            
            angulo_inicio = mapa.get("angulo_jugador", 0)
            rad_lado = math.radians(angulo_inicio - 90)
            ex = px + math.cos(rad_lado) * 60
            ey = py - math.sin(rad_lado) * 60
            
            n = len(self.circuito.puntos_ruta_ia)
            cp_indices = [n // 4, n // 2, (3 * n) // 4, 0]
            self.checkpoints = []
            for idx in cp_indices:
                cx, cy = self.circuito.puntos_ruta_ia[idx]
                self.checkpoints.append(pygame.Rect(cx - 100, cy - 100, 200, 200))
        else:
            px, py = mapa["pos_jugador"]
            ex, ey = mapa["pos_enemigo"]
            self.checkpoints = [pygame.Rect(*cp) for cp in mapa["checkpoints"]]

        try:
            sonido_motor = pygame.mixer.Sound(carro.get("audio", ""))
            sonido_motor.set_volume(0.3)
        except Exception:
            sonido_motor = None
            
        self.jugador = Jugador(px, py, stats=carro, sonido_motor=sonido_motor)
        self.jugador.angulo            = mapa.get("angulo_jugador", 0)
        self.jugador.checkpoint_actual = 0
        self.grupo_sprites.add(self.jugador)

        enemy_idx        = (self.carro_idx + 1) % len(CARROS)
        self.enemigo_car = CARROS[enemy_idx]
        if hasattr(self.circuito, "puntos_ruta_ia") and self.circuito.puntos_ruta_ia:
            ruta_ia = self.circuito.puntos_ruta_ia
        else:
            ruta_ia = mapa["ruta_enemigo"]

        self.enemigo     = Enemigo(
            ex, ey,
            ruta_ia,
            stats              = self.enemigo_car,
            jugador_referencia = self.jugador,
        )
        self.enemigo.checkpoint_actual = 0
        self.enemigo.angulo = self.jugador.angulo
        rad = math.radians(self.jugador.angulo)
        self.jugador.dir_movimiento = Vector2(math.cos(rad), -math.sin(rad))
        self.enemigo.dir_movimiento = Vector2(math.cos(rad), -math.sin(rad))
        self.jugador.rotar_imagen()
        self.enemigo.rotar_imagen()
        self.grupo_sprites.add(self.enemigo)

        self.camara = Camara(ANCHO, ALTO)

        pygame.mixer.music.stop()
        
        self.tiempo_conteo = pygame.time.get_ticks()
        self.estado = "CONTEO"

    # ── Eventos ──────────────────────────────────────────────────────────────

    def procesar_eventos(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.estado = "SALIR"
            elif ev.type == pygame.KEYDOWN:
                self._tecla(ev.key)

    def _tecla(self, key):
        confirmar = key in (pygame.K_RETURN, pygame.K_SPACE)
        volver    = key == pygame.K_ESCAPE

        if self.estado == "MENU":
            if confirmar:
                self.estado = "SELECCION_CARRO"
            elif volver:
                self.estado = "SALIR"

        elif self.estado == "SELECCION_CARRO":
            if key == pygame.K_LEFT:
                self.carro_idx = (self.carro_idx - 1) % len(CARROS)
            elif key == pygame.K_RIGHT:
                self.carro_idx = (self.carro_idx + 1) % len(CARROS)
            elif confirmar:
                self.estado = "SELECCION_MAPA"
            elif volver:
                self.estado = "MENU"

        elif self.estado == "SELECCION_MAPA":
            if key == pygame.K_LEFT:
                self.mapa_idx = (self.mapa_idx - 1) % len(MAPAS)
            elif key == pygame.K_RIGHT:
                self.mapa_idx = (self.mapa_idx + 1) % len(MAPAS)
            elif confirmar:
                self.iniciar_partida()
            elif volver:
                self.estado = "SELECCION_CARRO"

        elif self.estado in ("VICTORIA", "DERROTA"):
            if confirmar or volver:
                self.estado = "MENU"
                pygame.mixer.music.play(-1)

        elif self.estado == "CONTEO":
            if volver:
                self.estado = "MENU"
                if self.jugador and self.jugador.sonido_motor: self.jugador.sonido_motor.stop()
                pygame.mixer.music.play(-1)

        elif self.estado == "JUGANDO":
            if volver:
                self.estado = "MENU"
                if self.jugador and self.jugador.sonido_motor: self.jugador.sonido_motor.stop()
                pygame.mixer.music.play(-1)

    # ── Lógica de juego ──────────────────────────────────────────────────────

    def verificar_checkpoints(self, vehiculo, es_jugador):
        cp = self.checkpoints[vehiculo.checkpoint_actual]
        if vehiculo.rect.colliderect(cp):
            vehiculo.checkpoint_actual += 1
            if vehiculo.checkpoint_actual >= len(self.checkpoints):
                vehiculo.checkpoint_actual = 0
                if es_jugador:
                    self.vueltas_jugador += 1
                    if self.vueltas_jugador == self.vueltas_para_ganar - 1:
                        self.t_ultima_vuelta = pygame.time.get_ticks()
                    if self.vueltas_jugador >= self.vueltas_para_ganar:
                        self.tiempo_fin = pygame.time.get_ticks()
                        self.estado = "VICTORIA"
                        if self.jugador.sonido_motor: self.jugador.sonido_motor.stop()
                else:
                    self.vueltas_enemigo += 1
                    if self.vueltas_enemigo >= self.vueltas_para_ganar:
                        self.tiempo_fin = pygame.time.get_ticks()
                        self.estado = "DERROTA"
                        if self.jugador.sonido_motor: self.jugador.sonido_motor.stop()

    def obtener_posiciones(self):
        score_j = self.vueltas_jugador * 10000 + self.jugador.checkpoint_actual * 1000
        score_e = self.vueltas_enemigo * 10000 + self.enemigo.checkpoint_actual * 1000
        datos = [
            {"nombre": "TÚ",    "score": score_j,
             "vueltas": self.vueltas_jugador, "cp": self.jugador.checkpoint_actual,
             "color": CARROS[self.carro_idx]["color"], "es_jugador": True},
            {"nombre": "RIVAL", "score": score_e,
             "vueltas": self.vueltas_enemigo, "cp": self.enemigo.checkpoint_actual,
             "color": self.enemigo_car["color"] if self.enemigo_car else AZUL,
             "es_jugador": False},
        ]
        return sorted(datos, key=lambda d: d["score"], reverse=True)

    def actualizar(self):
        if self.estado == "CONTEO":
            elapsed = pygame.time.get_ticks() - self.tiempo_conteo
            self.camara.actualizar(self.jugador, self.circuito.ancho_px, self.circuito.alto_px)
            if elapsed >= 4000:
                self.tiempo_inicio = pygame.time.get_ticks()
                self.estado = "JUGANDO"
            return

        for sprite in self.grupo_sprites:
            desp    = (int(sprite.rect.x), int(sprite.rect.y))
            terreno = self.circuito.comprobar_colision(sprite.mask, desp)
            sprite.update(terreno)
            self.verificar_checkpoints(sprite, es_jugador=(sprite == self.jugador))
        self.camara.actualizar(self.jugador, self.circuito.ancho_px, self.circuito.alto_px)

    # ── Dibujo principal ──────────────────────────────────────────────────────

    def dibujar(self):
        self.tiempo_anim += 1

        if   self.estado == "MENU":              self._dibujar_menu()
        elif self.estado == "SELECCION_CARRO":   self._dibujar_sel_carro()
        elif self.estado == "SELECCION_MAPA":    self._dibujar_sel_mapa()
        elif self.estado == "CONTEO":            self._dibujar_conteo()
        elif self.estado == "JUGANDO":           self._dibujar_juego()
        elif self.estado in ("VICTORIA","DERROTA"): self._dibujar_resultado()

        pygame.display.flip()

    # ── Utilidades visuales ───────────────────────────────────────────────────

    def _fondo_animado(self):
        self.pantalla.fill(COLOR_FONDO)
        t = self.tiempo_anim
        for i in range(0, ANCHO, 60):
            c = 22 + int(7 * math.sin(t * 0.015 + i * 0.05))
            pygame.draw.line(self.pantalla, (c, c+8, c+22), (i, 0), (i, ALTO), 1)
        for j in range(0, ALTO, 60):
            pygame.draw.line(self.pantalla, (22, 30, 52), (0, j), (ANCHO, j), 1)

    def _boton(self, texto, cx, cy, w, h, col_fondo, col_texto, borde=None):
        rect = pygame.Rect(cx - w//2, cy - h//2, w, h)
        pygame.draw.rect(self.pantalla, col_fondo, rect, border_radius=14)
        pygame.draw.rect(self.pantalla, borde or COLOR_PANEL_BORDE, rect, 2, border_radius=14)
        s = self.f_media.render(texto, True, col_texto)
        self.pantalla.blit(s, (cx - s.get_width()//2, cy - s.get_height()//2))

    def _barra(self, x, y, w, h, valor, maximo, color):
        pygame.draw.rect(self.pantalla, (32, 38, 62), (x, y, w, h), border_radius=5)
        fill = int(w * valor / maximo)
        if fill > 0:
            pygame.draw.rect(self.pantalla, color, (x, y, fill, h), border_radius=5)

    def _mini_carro(self, cx, cy, carro_info, angulo=0, escala=1.0):
        surf = None
        if isinstance(carro_info, dict) and "imagen" in carro_info:
            target_w = int(48 * escala)
            idx = carro_info.get("sprite_idx", 0)
            surf = cargar_imagen_carro(carro_info["imagen"], ancho_deseado=target_w, sprite_idx=idx)

        if surf is None:
            color = carro_info["color"] if isinstance(carro_info, dict) else carro_info
            w, h = int(48*escala), int(22*escala)
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            surf.fill(color)
            pw = int(14*escala); ph = int(12*escala)
            pygame.draw.rect(surf, BLANCO, (w-pw-2, (h-ph)//2, pw, ph))

        rot = pygame.transform.rotate(surf, angulo)
        self.pantalla.blit(rot, (cx - rot.get_width()//2, cy - rot.get_height()//2))

    # ── MENÚ PRINCIPAL ────────────────────────────────────────────────────────

    def _dibujar_menu(self):
        self.pantalla.blit(self.bg_menu, (0, 0))
            
        t     = self.tiempo_anim
        pulse = 0.88 + 0.12 * math.sin(t * 0.04)

        # ── Bloque central ──
        centro_y = ALTO // 2

        sub = self.f_mini.render("T O P - D O W N   .   P O O   E D I T I O N", True, COLOR_ACENTO2)
        self.pantalla.blit(sub, (ANCHO//2 - sub.get_width()//2, centro_y - 140))

        pygame.draw.line(self.pantalla, COLOR_PANEL_BORDE,
                         (ANCHO//2 - 220, centro_y - 116),
                         (ANCHO//2 + 220, centro_y - 116), 1)

        tx = ANCHO//2 - self.img_logo.get_width()//2
        self.pantalla.blit(self.img_logo, (tx, centro_y - 100 - self.img_logo.get_height()//2))

        pygame.draw.line(self.pantalla, COLOR_PANEL_BORDE,
                         (ANCHO//2 - 220, centro_y - 8),
                         (ANCHO//2 + 220, centro_y - 8), 1)

        self._boton("INICIAR JUEGO", ANCHO//2, centro_y + 55,  280, 58, (22, 34, 72), COLOR_ACENTO,  COLOR_ACENTO)
        self._boton("SALIR",         ANCHO//2, centro_y + 130, 180, 46, GRIS_OSCURO,  GRIS_CLARO)

        hint = self.f_mini.render("ENTER / ESPACIO para empezar   .   ESC para salir", True, (55, 62, 90))
        self.pantalla.blit(hint, (ANCHO//2 - hint.get_width()//2, ALTO - 24))



    # ── SELECCIÓN DE CARRO ────────────────────────────────────────────────────

    def _dibujar_sel_carro(self):
        self.pantalla.blit(self.bg_taller, (0, 0))
            
        titulo = self.f_grande.render("ELIGE TU VEHICULO", True, COLOR_ACENTO)
        self.pantalla.blit(titulo, (ANCHO//2 - titulo.get_width()//2, 30))

        n = len(CARROS); card_w = 220; card_h = 310
        spacing = (ANCHO - n*card_w) // (n+1)

        for i, carro in enumerate(CARROS):
            x = spacing + i*(card_w+spacing)
            y = (ALTO-card_h)//2 + 10
            self._tarjeta_carro(x, y, card_w, card_h, carro, i == self.carro_idx)

        sx = spacing + self.carro_idx*(card_w+spacing) + card_w//2
        ay = (ALTO-card_h)//2 + 10 - 22 + int(5*math.sin(self.tiempo_anim*0.1))
        pygame.draw.polygon(self.pantalla, COLOR_ACENTO,
                            [(sx, ay+14), (sx-10, ay), (sx+10, ay)])

        hint = self.f_mini.render("IZQUIERDA / DERECHA para seleccionar   ·   ENTER para confirmar   ·   ESC para volver", True, GRIS)
        self.pantalla.blit(hint, (ANCHO//2 - hint.get_width()//2, ALTO-24))

    def _tarjeta_carro(self, x, y, w, h, carro, sel):
        bg  = (28,40,75) if sel else (18,23,40)
        brd = COLOR_ACENTO if sel else COLOR_PANEL_BORDE
        pygame.draw.rect(self.pantalla, bg,  (x, y, w, h), border_radius=18)
        pygame.draw.rect(self.pantalla, brd, (x, y, w, h), 3 if sel else 1, border_radius=18)

        self._mini_carro(x+w//2, y+45, carro, escala=1.8)

        nm = self.f_media.render(carro["nombre"], True, BLANCO if sel else GRIS_CLARO)
        self.pantalla.blit(nm, (x+w//2 - nm.get_width()//2, y+85))

        dc = self.f_mini.render(carro["descripcion"], True, GRIS)
        self.pantalla.blit(dc, (x+w//2 - dc.get_width()//2, y+118))

        bx, by, bw, bh = x+20, y+148, w-40, 11
        for etiq, val, col in [
            ("Veloc.", carro["stat_veloc"], (220,80,80)),
            ("Acel.",  carro["stat_acel"],  (80,180,220)),
            ("Giro",   carro["stat_giro"],  (80,220,120)),
        ]:
            lbl = self.f_mini.render(etiq, True, GRIS_CLARO)
            self.pantalla.blit(lbl, (bx, by))
            self._barra(bx+55, by+2, bw-55, bh, val, 10, col)
            num = self.f_mini.render(str(val), True, GRIS_CLARO)
            self.pantalla.blit(num, (bx+bw-num.get_width(), by))
            by += 32

        if sel:
            pygame.draw.rect(self.pantalla, COLOR_ACENTO,
                             (x+20, y+h-14, w-40, 4), border_radius=2)

    # ── SELECCIÓN DE MAPA ─────────────────────────────────────────────────────

    def _dibujar_sel_mapa(self):
        self.pantalla.blit(self.bg_taller, (0, 0))
            
        titulo = self.f_grande.render("ELIGE EL CIRCUITO", True, COLOR_ACENTO)
        self.pantalla.blit(titulo, (ANCHO//2 - titulo.get_width()//2, 30))

        n = len(MAPAS); card_w = 360; card_h = 330
        spacing = (ANCHO - n*card_w) // (n+1)

        for i, mapa in enumerate(MAPAS):
            x = spacing + i*(card_w+spacing)
            y = (ALTO-card_h)//2 + 12
            self._tarjeta_mapa(x, y, card_w, card_h, mapa, i == self.mapa_idx, i)

        sx = spacing + self.mapa_idx*(card_w+spacing) + card_w//2
        ay = (ALTO-card_h)//2 + 12 - 22 + int(5*math.sin(self.tiempo_anim*0.1))
        pygame.draw.polygon(self.pantalla, COLOR_ACENTO,
                            [(sx, ay+14), (sx-10, ay), (sx+10, ay)])

        hint = self.f_mini.render("IZQUIERDA / DERECHA para seleccionar   ·   ENTER para iniciar   ·   ESC para volver", True, GRIS)
        self.pantalla.blit(hint, (ANCHO//2 - hint.get_width()//2, ALTO-24))

    def _tarjeta_mapa(self, x, y, w, h, mapa, sel, idx):
        bg  = (28,40,75) if sel else (18,23,40)
        brd = COLOR_ACENTO if sel else COLOR_PANEL_BORDE
        pygame.draw.rect(self.pantalla, bg,  (x, y, w, h), border_radius=18)
        pygame.draw.rect(self.pantalla, brd, (x, y, w, h), 3 if sel else 1, border_radius=18)

        prev_rect = pygame.Rect(x+18, y+18, w-36, 168)
        self._preview_mapa(prev_rect, idx)

        nm = self.f_media.render(mapa["nombre"], True, BLANCO if sel else GRIS_CLARO)
        self.pantalla.blit(nm, (x+w//2 - nm.get_width()//2, y+198))

        dc = self.f_mini.render(mapa["descripcion"], True, GRIS)
        self.pantalla.blit(dc, (x+w//2 - dc.get_width()//2, y+232))

        vl = self.f_normal.render(f"  {mapa['vueltas']} vueltas para ganar", True, COLOR_ACENTO2)
        self.pantalla.blit(vl, (x+w//2 - vl.get_width()//2, y+258))

        if sel:
            pygame.draw.rect(self.pantalla, COLOR_ACENTO,
                             (x+20, y+h-14, w-40, 4), border_radius=2)

    def _preview_mapa(self, rect, idx):
        if idx < len(self.map_previews) and self.map_previews[idx]:
            self.pantalla.blit(self.map_previews[idx], rect.topleft)
            pygame.draw.rect(self.pantalla, (40,52,90), rect, 2, border_radius=10)
        else:
            pygame.draw.rect(self.pantalla, (22,28,50), rect, border_radius=10)
            pygame.draw.rect(self.pantalla, (40,52,90), rect, 1, border_radius=10)
            rx, ry, rw, rh = rect.x, rect.y, rect.width, rect.height

            if idx == 0:
                pygame.draw.rect(self.pantalla, (55,65,90), rect.inflate(-6,-6), 1, border_radius=8)
                pygame.draw.rect(self.pantalla, (34,110,34), (rx+rw//4, ry+rh//4, rw//2, rh//2), border_radius=6)
            else:
                pygame.draw.rect(self.pantalla, (55,65,90), rect.inflate(-6,-6), 1, border_radius=8)
                pygame.draw.rect(self.pantalla, (34,120,34), (rx+14, ry+14, rw//2-18, rh//2-14), border_radius=6)
                pygame.draw.rect(self.pantalla, (34,120,34), (rx+rw//2+4, ry+rh//2+8, rw//2-14, rh//2-18), border_radius=6)

            spx = rx + int((MAPAS[idx]["pos_jugador"][0] / 800) * rw)
            spy = ry + int((MAPAS[idx]["pos_jugador"][1] / 608) * rh)
            pygame.draw.circle(self.pantalla, COLOR_ACENTO, (spx, spy), 6)
            pygame.draw.circle(self.pantalla, NEGRO, (spx, spy), 6, 1)

    # ── CUENTA REGRESIVA ────────────────────────────────────────────────

    def _dibujar_conteo(self):
        self.pantalla.fill((30, 32, 35))
        if self.circuito and self.circuito.fondo:
            self.pantalla.blit(self.circuito.fondo,
                               self.camara.aplicar_rect(self.circuito.fondo.get_rect()))
        for sprite in self.grupo_sprites:
            self.pantalla.blit(sprite.image, self.camara.aplicar(sprite))

        elapsed     = pygame.time.get_ticks() - self.tiempo_conteo
        etapa       = elapsed // 1000
        ms_etapa    = elapsed % 1000

        textos = ["3", "2", "1", "YA!"]
        colores = [(255, 80, 80), (255, 190, 30), (80, 230, 80), COLOR_ACENTO]
        texto     = textos[min(etapa, 3)]
        color_num = colores[min(etapa, 3)]

        escala = min(1.0, ms_etapa / 180.0)
        alpha  = int(255 * min(1.0, (950 - ms_etapa) / 250.0)) if ms_etapa > 700 else 255

        tam = int(150 * escala + 20)
        f_num = pygame.font.SysFont("Arial", tam, bold=True)
        surf  = f_num.render(texto, True, color_num)
        surf.set_alpha(alpha)

        cx, cy = ANCHO // 2, ALTO // 2
        self.pantalla.blit(surf, (cx - surf.get_width() // 2, cy - surf.get_height() // 2))

        subtexto = "PREPÁRATE" if etapa < 3 else "A CORRER"
        sub_col  = GRIS_CLARO   if etapa < 3 else COLOR_ACENTO
        sub = self.f_media.render(subtexto, True, sub_col)
        sub.set_alpha(int(220 * escala))
        self.pantalla.blit(sub, (cx - sub.get_width() // 2, cy + 90))

    # ── JUGANDO ────────────────────────────────────────────────────

    def _dibujar_juego(self):
        self.pantalla.fill((30, 32, 35))
        if self.circuito and self.circuito.fondo:
            self.pantalla.blit(self.circuito.fondo,
                               self.camara.aplicar_rect(self.circuito.fondo.get_rect()))
        for sprite in self.grupo_sprites:
            self.pantalla.blit(sprite.image, self.camara.aplicar(sprite))

        self._dibujar_hud()

    def _dibujar_hud(self):
        """HUD flotante minimalista: vueltas + posiciones en esquina superior izquierda."""
        vueltas_actuales = self.vueltas_jugador + 1
        es_ultima = (vueltas_actuales == self.vueltas_para_ganar)

        color_vueltas = COLOR_ACENTO if es_ultima else BLANCO
        txt_vuelta = f"{vueltas_actuales} / {self.vueltas_para_ganar}"
        lbl_vuelta = self.f_hud.render("VUELTA", True, GRIS_CLARO)
        num_vuelta = self.f_grande.render(txt_vuelta, True, color_vueltas)
        self.pantalla.blit(lbl_vuelta, (18, 14))
        self.pantalla.blit(num_vuelta, (18, 34))

        pos_lista = self.obtener_posiciones()
        y_pos = 80
        colores_pos = [COLOR_ORO, COLOR_PLATA]
        for i, datos in enumerate(pos_lista):
            col_medalla = colores_pos[i]
            
            tarjeta_rect = pygame.Rect(18, y_pos, 140, 36)
            pygame.draw.rect(self.pantalla, (20, 26, 48), tarjeta_rect, border_radius=8)
            pygame.draw.rect(self.pantalla, col_medalla, tarjeta_rect, 2, border_radius=8)

            s_pos  = self.f_hud.render(f"{i+1}°", True, col_medalla)
            s_nom  = self.f_mini.render(datos["nombre"], True,
                                        BLANCO if datos["es_jugador"] else GRIS_CLARO)
            pygame.draw.circle(self.pantalla, datos["color"], (32, y_pos + 18), 5)
            
            self.pantalla.blit(s_pos, (46, y_pos + 6))
            self.pantalla.blit(s_nom, (72, y_pos + 8))
            
            y_pos += 46

        esc = self.f_mini.render("ESC - Menu", True, (55, 62, 90))
        self.pantalla.blit(esc, (18, ALTO - 22))

        if self.t_ultima_vuelta > 0:
            elapsed_uv = pygame.time.get_ticks() - self.t_ultima_vuelta
            duracion   = 2500
            if elapsed_uv < duracion:
                if elapsed_uv < 300:
                    alpha_uv = int(255 * elapsed_uv / 300)
                elif elapsed_uv > duracion - 600:
                    alpha_uv = int(255 * (duracion - elapsed_uv) / 600)
                else:
                    alpha_uv = 255

                f_uv   = pygame.font.SysFont("Arial", 52, bold=True)
                surf_uv = f_uv.render("ULTIMA VUELTA", True, COLOR_ACENTO)
                surf_uv.set_alpha(alpha_uv)
                cx = ANCHO // 2
                self.pantalla.blit(surf_uv, (cx - surf_uv.get_width() // 2, ALTO // 2 - 30))
            else:
                self.t_ultima_vuelta = 0



    # ── VICTORIA / DERROTA ─────────────────────────────────────────────────

    def _dibujar_resultado(self):
        self._fondo_animado()
        gano  = (self.estado == "VICTORIA")
        texto = "VICTORIA" if gano else "DERROTA"
        col   = COLOR_ORO if gano else ROJO
        pulse = 0.75 + 0.25 * math.sin(self.tiempo_anim * 0.06)
        cy    = ALTO//2 - 110

        tsurf = self.f_titulo.render(texto, True, col)
        tx    = ANCHO//2 - tsurf.get_width()//2
        self.pantalla.blit(tsurf, (tx, cy))

        t_ms = (self.tiempo_fin - self.tiempo_inicio) if self.tiempo_fin > 0 else 0
        mins, segs = divmod(t_ms // 1000, 60)
        tt = self.f_media.render(f"Tiempo:  {mins:02d}:{segs:02d}", True, GRIS_CLARO)
        self.pantalla.blit(tt, (ANCHO//2 - tt.get_width()//2, cy+100))

        info_y = cy + 148
        for txt, col2 in [
            (f"Carro:     {CARROS[self.carro_idx]['nombre']}", GRIS),
            (f"Circuito:  {MAPAS[self.mapa_idx]['nombre']}",   GRIS),
        ]:
            s = self.f_normal.render(txt, True, col2)
            self.pantalla.blit(s, (ANCHO//2 - s.get_width()//2, info_y))
            info_y += 33

        self._boton("MENU PRINCIPAL", ANCHO//2, ALTO//2 + 130, 290, 58,
                    (20, 30, 65), COLOR_ACENTO, COLOR_ACENTO)
        hint = self.f_mini.render("ENTER / ESC para volver al menu", True, (55, 62, 90))
        self.pantalla.blit(hint, (ANCHO//2 - hint.get_width()//2, ALTO - 24))

    # ── BUCLE PRINCIPAL ───────────────────────────────────────────────────────

    def ejecutar(self):
        while self.estado != "SALIR":
            self.reloj.tick(FPS)
            self.procesar_eventos()
            if self.estado in ("JUGANDO", "CONTEO"):
                self.actualizar()
            self.dibujar()
        pygame.quit()


if __name__ == "__main__":
    juego = GestorJuego()
    juego.ejecutar()
