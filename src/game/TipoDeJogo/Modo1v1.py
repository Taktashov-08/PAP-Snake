# Descrição: Lógica do Modo Multijogador 1v1 (Local). 
# Gere duas instâncias de cobras, colisões mútuas e um sistema de prontidão (ready check).
# src/game/TipoDeJogo/Modo1v1.py
import pygame
from game.snake import Snake
from game.food import Food

class Modo1v1:
    def __init__(self, engine):
        self.engine = engine
        self.started = False
        
        # ── Variáveis de Controlo do Countdown ─────────────────────
        self.p1_ready = False
        self.p2_ready = False
        self.countdown_active = False
        self.countdown_val = 3
        self.last_tick = 0 

        # Conjunto para evitar que comida ou cobras nasçam no mesmo sítio
        ocupado_pixels = set()

        # ── Configuração do Player 1 (Verde) ───────────────────────
        spawn_p1 = self.engine.mapa.obter_spawn_player(1)
        self.snake = Snake(start_pos=spawn_p1, block_size=self.engine.block)
        self.snake.color = (0, 255, 0) 
        ocupado_pixels.update(self.snake.segments)

        # ── Configuração do Player 2 (Azul) ────────────────────────
        spawn_p2 = self.engine.mapa.obter_spawn_player(2)
        self.snake2 = Snake(start_pos=spawn_p2, block_size=self.engine.block)
        self.snake2.color = (0, 100, 255) 
        ocupado_pixels.update(self.snake2.segments)

        # ── Inicialização das Comidas ─────────────────────────────
        self.foods = []
        obstaculos_pix = set(self.engine.mapa.obstaculos_pixels())
        # Spawna 2 unidades de comida inicialmente
        for _ in range(2):
            f = Food(self.engine.play_rect, self.engine.block)
            outras = {fd.pos for fd in self.foods if fd.pos}
            f.spawn(ocupado_pixels | outras, obstaculos_pix)
            self.foods.append(f)

    def handle_event(self, event):
        """Captura inputs de ambos os jogadores e ativa o estado 'Pronto'."""
        if event.type == pygame.KEYDOWN:
            # Player 1 (Controlos: WASD)
            if event.key == pygame.K_w: self.snake.set_direction(0, -1); self.p1_ready = True
            elif event.key == pygame.K_s: self.snake.set_direction(0, 1); self.p1_ready = True
            elif event.key == pygame.K_a: self.snake.set_direction(-1, 0); self.p1_ready = True
            elif event.key == pygame.K_d: self.snake.set_direction(1, 0); self.p1_ready = True

            # Player 2 (Controlos: Setas)
            if event.key == pygame.K_UP: self.snake2.set_direction(0, -1); self.p2_ready = True
            elif event.key == pygame.K_DOWN: self.snake2.set_direction(0, 1); self.p2_ready = True
            elif event.key == pygame.K_LEFT: self.snake2.set_direction(-1, 0); self.p2_ready = True
            elif event.key == pygame.K_RIGHT: self.snake2.set_direction(1, 0); self.p2_ready = True

    def update(self):
        """Atualiza a lógica: cronómetro de início, movimento e colisões."""
        
        # 1. Iniciar Countdown quando ambos carregam numa tecla de direção
        if self.p1_ready and self.p2_ready and not self.countdown_active and not self.started:
            self.countdown_active = True
            self.last_tick = pygame.time.get_ticks()

        # 2. Gestão do cronómetro (passagem de segundos)
        if self.countdown_active:
            agora = pygame.time.get_ticks()
            if agora - self.last_tick >= 1000:
                self.countdown_val -= 1
                self.last_tick = agora
                if self.countdown_val <= 0:
                    self.countdown_active = False
                    self.started = True

        # 3. Se o jogo ainda não começou, interrompe aqui (as cobras ficam paradas)
        if not self.started:
            return

        # 4. Movimento (Apenas após o Countdown)
        self.snake.update()
        self.snake2.update()

        head1 = self.snake.head_pos()
        head2 = self.snake2.head_pos()

        # ── Verificação de Colisões ──
        
        # Colisões com Paredes/Obstáculos do Mapa e Portais (Teleport)
        res1 = self.engine.mapa.verificar_colisao(head1)
        res2 = self.engine.mapa.verificar_colisao(head2)
        
        p1_dead = (res1 is True) # True significa morte por obstáculo
        p2_dead = (res2 is True)

        # Se o mapa devolver uma posição (tuplo), é um portal
        if isinstance(res1, tuple): self.snake.set_head_pos(res1)
        if isinstance(res2, tuple): self.snake2.set_head_pos(res2)

        # Colisão Frontal (Cabeça com Cabeça)
        if head1 == head2:
            self.engine.game_over_1v1("Empate (Choque Frontal)")
            return

        # Colisão com o corpo do adversário ou próprio corpo
        if head1 in self.snake2.segments: p1_dead = True
        if head2 in self.snake.segments: p2_dead = True
        if self.snake.collides_self(): p1_dead = True
        if self.snake2.collides_self(): p2_dead = True

        # ── Determinação do Vencedor ──
        if p1_dead and p2_dead: self.engine.game_over_1v1("Empate")
        elif p1_dead: self.engine.game_over_1v1("Vitória P2")
        elif p2_dead: self.engine.game_over_1v1(f"Vitória {self.engine.player_name}")
        
        if not self.engine.running: return

        # ── Lógica da Comida ──
        for comida in self.foods:
            if head1 == comida.pos:
                self.snake.grow()
                self.food_spawn_safe(comida)
            if head2 == comida.pos:
                self.snake2.grow()
                self.food_spawn_safe(comida)

    def food_spawn_safe(self, food_object):
        """Garante que a comida nasce num lugar livre de cobras, obstáculos e outra comida."""
        occupied = set(self.snake.segments) | set(self.snake2.segments)
        for f in self.foods:
            if f != food_object and f.pos: occupied.add(f.pos)
        food_object.spawn(occupied, set(self.engine.mapa.obstaculos_pixels()))

    def draw(self, surface):
        """Desenha as cobras, comida e a interface de prontidão/countdown."""
        self.snake.draw(surface)
        self.snake2.draw(surface)
        for f in self.foods:
            try: f.draw(surface)
            except: pass

        # ── Interface de Utilizador (UI) durante o Lobby/Countdown ──
        f_grande = pygame.font.SysFont(None, 80)
        f_pequena = pygame.font.SysFont(None, 30)
        
        largura = surface.get_width()
        altura = surface.get_height()
        cx, cy = largura // 2, altura // 2

        # Mensagens de espera antes de ambos estarem prontos
        if not self.p1_ready or not self.p2_ready:
            msg = f_pequena.render("Escolham a vossa direção!", True, (255, 255, 255))
            surface.blit(msg, (cx - msg.get_width()//2, cy - 80))
            
            # Status P1 (Esquerda)
            p1_txt = "PRONTO!" if self.p1_ready else "P1 (WASD): Espera..."
            s1 = f_pequena.render(p1_txt, True, (0, 255, 0))
            surface.blit(s1, (largura // 4 - s1.get_width() // 2, cy + 20))
            
            # Status P2 (Direita)
            p2_txt = "PRONTO!" if self.p2_ready else f"{self.engine.player2_name} (Setas): Espera..."
            s2 = f_pequena.render(p2_txt, True, (0, 150, 255))
            surface.blit(s2, (3 * largura // 4 - s2.get_width() // 2, cy + 20))

        # Desenha o número da contagem decrescente no centro
        elif self.countdown_active:
            num = f_grande.render(str(self.countdown_val), True, (255, 200, 0))
            surface.blit(num, (cx - num.get_width()//2, cy - num.get_height()//2))