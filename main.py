import pygame
import sys
import random
import os

pygame.init()

# Configurações da tela
LARGURA = 1000
ALTURA = 600
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Makima vs Chainsaw Man")

# Cores
AZUL = (0, 0, 255)
VERMELHO = (255, 0, 0)
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)

# FPS
clock = pygame.time.Clock()
FPS = 40

# --- Carregar Recursos ---
# Fundo e música
# A LINHA ABAIXO FOI CORRIGIDA. O CAMINHO RELATIVO AGORA ESTÁ CORRETO.
fundo = pygame.image.load("imagens/fundo/fundoPixelArt.png")
fundo = pygame.transform.scale(fundo, (LARGURA, ALTURA))
pygame.mixer.music.load("audio/music/musicafundo.wav")
pygame.mixer.music.play(-1)

# Fonte para o texto
fonte = pygame.font.Font(None, 50)

# Função para carregar sprites
def carregar_sprites(pasta, escala=None):
    frames = []
    for arquivo in sorted(os.listdir(pasta)):
        if arquivo.endswith(".png"):
            img = pygame.image.load(os.path.join(pasta, arquivo)).convert_alpha()
            if escala:
                img = pygame.transform.scale(img, escala)
            frames.append(img)
    return frames

# --- Classes dos Personagens ---
class Jogador(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.anim = {
            "idle": carregar_sprites("imagens/makima/idle", escala=(80, 120)),
            "walk": carregar_sprites("imagens/makima/walk", escala=(80, 120)),
            "jump": carregar_sprites("imagens/makima/jump", escala=(80, 120)),
            "attack1": carregar_sprites("imagens/makima/attack1", escala=(100, 130)),
            "attack2": carregar_sprites("imagens/makima/attack2", escala=(100, 130)),
            "dead": carregar_sprites("imagens/makima/dead", escala=(80, 120)),
        }
        self.estado = "idle"
        self.frame = 0
        self.image = self.anim[self.estado][self.frame]
        self.rect = self.image.get_rect()
        self.rect.midbottom = (200, ALTURA - 50)
        self.vel_y = 0
        self.no_chao = False
        self.direita = True
        self.atacando = False
        self.tempo_ataque = 0
        self.vida = 300
        self.vida_max = 300
        self.morto = False
        self.pode_atacar_1 = True
        self.pode_atacar_2 = True
        self.cooldown_ataque_2 = 40
        self.hitbox_ataque_2 = None

    def mudar_estado(self, estado):
        if self.estado != estado:
            self.estado = estado
            self.frame = 0

    def update(self, grupo_projeteis):
        # Morte
        if self.vida <= 0:
            self.mudar_estado("dead")
            self.morto = True
            if self.frame < len(self.anim["dead"]) - 1:
                self.frame += 0.2
            self.image = self.anim["dead"][int(min(self.frame, len(self.anim["dead"]) - 1))]
            return

        keys = pygame.key.get_pressed()
        
        # Lógica de pulo
        if keys[pygame.K_UP] and self.no_chao:
            self.vel_y = -15
            self.no_chao = False
            self.mudar_estado("jump")
        
        # Se não estiver atacando E não estiver no ar, permite a mudança de estado de movimento
        if not self.atacando and self.no_chao:
            if keys[pygame.K_LEFT]:
                self.rect.x -= 5
                self.direita = False
                self.mudar_estado("walk")
            elif keys[pygame.K_RIGHT]:
                self.rect.x += 5
                self.direita = True
                self.mudar_estado("walk")
            else:
                self.mudar_estado("idle")

        # Se não estiver no chão, o estado é sempre "jump"
        if not self.no_chao:
            self.mudar_estado("jump")

        # Ataques
        if not self.atacando:
            if keys[pygame.K_a] and self.pode_atacar_1:
                self.mudar_estado("attack1")
                self.atacando = True
                self.tempo_ataque = 15
                self.pode_atacar_1 = False
                projetil = ProjetilMakima(self.rect.centerx, self.rect.centery, self.direita)
                grupo_projeteis.add(projetil)
                
            elif keys[pygame.K_s] and self.pode_atacar_2:
                self.mudar_estado("attack2")
                self.atacando = True
                self.tempo_ataque = self.cooldown_ataque_2
                self.pode_atacar_2 = False

        if self.atacando:
            self.tempo_ataque -= 1
            if self.tempo_ataque <= 0:
                self.atacando = False
                self.pode_atacar_1 = True
                self.pode_atacar_2 = True

        # Gravidade
        self.vel_y += 1
        self.rect.y += self.vel_y
        if self.rect.bottom >= ALTURA - 50:
            self.rect.bottom = ALTURA - 50
            self.vel_y = 0
            self.no_chao = True
            # Se a animação de pulo estiver ativa, volte para ocioso ao tocar o chão
            if self.estado == "jump":
                self.mudar_estado("idle")

        # Impedir sair da tela
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > LARGURA:
            self.rect.right = LARGURA

        # Atualizar animação
        self.frame = (self.frame + 0.2) % len(self.anim[self.estado])
        self.image = self.anim[self.estado][int(self.frame)]
        if not self.direita:
            self.image = pygame.transform.flip(self.image, True, False)
        
        # Cria a hitbox do ataque 2 para checagem no loop principal
        self.hitbox_ataque_2 = None
        if self.atacando and self.estado == "attack2":
            if self.direita:
                largura = 180
                self.hitbox_ataque_2 = pygame.Rect(self.rect.right, self.rect.centery - 20, largura, 40)
            else:
                largura = 180
                self.hitbox_ataque_2 = pygame.Rect(self.rect.left - largura, self.rect.centery - 20, largura, 40)

    def desenhar(self, tela):
        tela.blit(self.image, self.rect)
        return self.hitbox_ataque_2

class ProjetilMakima(pygame.sprite.Sprite):
    def __init__(self, x, y, direcao_direita):
        super().__init__()
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.velocidade = 15
        if not direcao_direita:
            self.velocidade *= -1
        self.dano = 15
        self.empurrao = 15

    def update(self):
        self.rect.x += self.velocidade
        if self.rect.right < 0 or self.rect.left > LARGURA:
            self.kill()

class ChainsawMan(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.anim = {
            "idle": carregar_sprites("imagens/chainsaw/idle", escala=(100, 140)),
            "walk": carregar_sprites("imagens/chainsaw/walk", escala=(100, 140)),
            "jump": carregar_sprites("imagens/chainsaw/jump", escala=(100, 140)),
            "attack1": carregar_sprites("imagens/chainsaw/attack1", escala=(120, 150)),
            "attack2": carregar_sprites("imagens/chainsaw/attack2", escala=(120, 150)),
            "dead": carregar_sprites("imagens/chainsaw/dead", escala=(100, 140)),
        }
        self.estado = "idle"
        self.frame = 0
        self.image = self.anim[self.estado][self.frame]
        self.rect = self.image.get_rect()
        self.rect.midbottom = (800, ALTURA - 50)
        self.rect.y += 30
        self.vel_y = 0
        self.no_chao = False
        self.direita = False
        self.atacando = False
        self.tempo_ataque = 0
        self.cooldown_ataque = 90
        self.tempo_cooldown = 0
        self.vida = 400
        self.vida_max = 400
        self.morto = False
        self.hitbox_ataque_1 = None
        self.hitbox_ataque_2 = None

    def mudar_estado(self, estado):
        if self.estado != estado:
            self.estado = estado
            self.frame = 0

    def update(self, jogador):
        # Morte
        if self.vida <= 0:
            self.mudar_estado("dead")
            self.morto = True
            if self.frame < len(self.anim["dead"]) - 1:
                self.frame += 0.2
            self.image = self.anim["dead"][int(min(self.frame, len(self.anim["dead"]) - 1))]
            return

        # IA de movimento e pulo
        if not self.atacando and self.no_chao:
            distancia_x = self.rect.centerx - jogador.rect.centerx
            
            # IA de Pulo
            if abs(distancia_x) < 150 and random.randint(1, 100) < 3:
                self.vel_y = -15
                self.no_chao = False
                self.mudar_estado("jump")

            # IA de Movimento
            elif distancia_x > 50:
                self.rect.x -= 3
                self.direita = False
                self.mudar_estado("walk")
            elif distancia_x < -50:
                self.rect.x += 3
                self.direita = True
                self.mudar_estado("walk")
            else:
                self.mudar_estado("idle")

        # Ataque com cooldown
        if abs(self.rect.centerx - jogador.rect.centerx) < 80 and self.tempo_cooldown == 0:
            ataque_escolhido = random.choice(["attack1", "attack2"])
            self.mudar_estado(ataque_escolhido)
            self.atacando = True
            self.tempo_ataque = 30
            self.tempo_cooldown = self.cooldown_ataque

        if self.tempo_cooldown > 0:
            self.tempo_cooldown -= 1

        if self.atacando:
            self.tempo_ataque -= 1
            if self.tempo_ataque <= 0:
                self.atacando = False

        # Gravidade
        self.vel_y += 1
        self.rect.y += self.vel_y
        if self.rect.bottom >= ALTURA - 20:
            self.rect.bottom = ALTURA - 20
            self.vel_y = 0
            self.no_chao = True
            if self.estado == "jump":
                self.mudar_estado("idle")

        # Impedir sair da tela
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > LARGURA:
            self.rect.right = LARGURA

        # Atualizar animação
        self.frame = (self.frame + 0.2) % len(self.anim[self.estado])
        self.image = self.anim[self.estado][int(self.frame)]
        if not self.direita:
            self.image = pygame.transform.flip(self.image, True, False)
        
        # Cria as hitboxes dos ataques
        self.hitbox_ataque_1 = None
        self.hitbox_ataque_2 = None
        if self.atacando and self.estado == "attack1":
            if self.direita:
                largura = 100
                self.hitbox_ataque_1 = pygame.Rect(self.rect.right, self.rect.centery - 40, largura, 80)
            else:
                largura = 100
                self.hitbox_ataque_1 = pygame.Rect(self.rect.left - largura, self.rect.centery - 40, largura, 80)
        elif self.atacando and self.estado == "attack2":
            if self.direita:
                largura = 150
                self.hitbox_ataque_2 = pygame.Rect(self.rect.right, self.rect.centery - 40, largura, 80)
            else:
                largura = 150
                self.hitbox_ataque_2 = pygame.Rect(self.rect.left - largura, self.rect.centery - 40, largura, 80)


    def desenhar(self, tela):
        tela.blit(self.image, self.rect)
        return self.hitbox_ataque_1, self.hitbox_ataque_2

# --- Funções do Jogo ---
def desenhar_barras():
    # Barra Makima
    pygame.draw.rect(tela, PRETO, (50, 20, 200, 20))
    largura_makima = int(200 * (jogador.vida / jogador.vida_max))
    pygame.draw.rect(tela, VERMELHO, (50, 20, largura_makima, 20))

    # Barra Chainsaw
    pygame.draw.rect(tela, PRETO, (LARGURA - 250, 20, 200, 20))
    largura_chainsaw = int(200 * (chainsaw.vida / chainsaw.vida_max))
    pygame.draw.rect(tela, AZUL, (LARGURA - 250, 20, largura_chainsaw, 20))

def mostrar_mensagem(texto):
    superficie_texto = fonte.render(texto, True, BRANCO)
    retangulo_texto = superficie_texto.get_rect(center=(LARGURA // 2, ALTURA // 2))
    tela.blit(superficie_texto, retangulo_texto)
    pygame.display.flip()
    pygame.time.delay(3000)

def reiniciar_jogo():
    global jogador, chainsaw, vencedor, musica_tocando, grupo_projeteis, pausado
    jogador = Jogador()
    chainsaw = ChainsawMan()
    grupo_projeteis.empty()
    vencedor = None
    pausado = False
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.play(-1)

# --- Criar objetos ---
jogador = Jogador()
chainsaw = ChainsawMan()
grupo_projeteis = pygame.sprite.Group()
vencedor = None
musica_tocando = True
pausado = False

# --- Loop principal ---
rodando = True
while rodando:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                reiniciar_jogo()
            if event.key == pygame.K_p:
                pausado = not pausado

    # Lógica de jogo só executa se não estiver pausado
    if not pausado:
        if not jogador.morto and not chainsaw.morto:
            jogador.update(grupo_projeteis)
            chainsaw.update(jogador)
            grupo_projeteis.update()

            # Desenhar
            tela.blit(fundo, (0, 0))
            desenhar_barras()
            
            hitbox_j2 = jogador.desenhar(tela)
            hitbox_c1, hitbox_c2 = chainsaw.desenhar(tela)
            grupo_projeteis.draw(tela)

            # Colisões de ataques
            if hitbox_j2 and chainsaw.rect.colliderect(hitbox_j2) and not chainsaw.morto:
                if not chainsaw.atacando:
                    chainsaw.vida -= 5
                    if jogador.direita:
                        chainsaw.rect.x += 10
                    else:
                        chainsaw.rect.x -= 10
                    print("Chainsaw levou dano! Vida:", chainsaw.vida)
            
            if hitbox_c1 and jogador.rect.colliderect(hitbox_c1) and not jogador.morto:
                if not jogador.atacando:
                    jogador.vida -= 5
                    if chainsaw.direita:
                        jogador.rect.x += 10
                    else:
                        jogador.rect.x -= 10
                    print("Makima levou dano (Ataque 1)! Vida:", jogador.vida)

            if hitbox_c2 and jogador.rect.colliderect(hitbox_c2) and not jogador.morto:
                if not jogador.atacando:
                    jogador.vida -= 10 
                    if chainsaw.direita:
                        jogador.rect.x += 20
                    else:
                        jogador.rect.x -= 20
                    print("Makima levou dano (Ataque 2)! Vida:", jogador.vida)

            # Colisão dos projéteis da Makima
            colisoes = pygame.sprite.spritecollide(chainsaw, grupo_projeteis, True)
            for projetil in colisoes:
                chainsaw.vida -= projetil.dano
                if projetil.velocidade > 0:
                    chainsaw.rect.x += projetil.empurrao
                else:
                    chainsaw.rect.x -= projetil.empurrao
                print(f"Chainsaw foi atingido por projétil! Dano: {projetil.dano}, Vida: {chainsaw.vida}")

            pygame.display.flip()
        else:
            # Lógica de fim de jogo
            tela.blit(fundo, (0, 0))
            jogador.desenhar(tela)
            chainsaw.desenhar(tela)
            desenhar_barras()
            
            if vencedor is None:
                if jogador.vida <= 0:
                    vencedor = "Chainsaw Man"
                    pygame.mixer.music.stop()
                elif chainsaw.vida <= 0:
                    vencedor = "Makima"
                    pygame.mixer.music.stop()

            if vencedor:
                if vencedor == "Makima":
                    texto_vencedor = "Vencedor: MAKIMA"
                else:
                    texto_vencedor = "Vencedor: CHAINSAW MAN"
                superficie_texto = fonte.render(texto_vencedor, True, BRANCO)
                retangulo_texto = superficie_texto.get_rect(center=(LARGURA // 2, ALTURA // 2))
                tela.blit(superficie_texto, retangulo_texto)
                
                texto_reiniciar = fonte.render("Pressione 'R' para Reiniciar", True, BRANCO)
                retangulo_reiniciar = texto_reiniciar.get_rect(center=(LARGURA // 2, ALTURA // 2 + 50))
                tela.blit(texto_reiniciar, retangulo_reiniciar)

            pygame.display.flip()
            
    else: # Se o jogo estiver pausado
        tela.blit(fundo, (0, 0))
        jogador.desenhar(tela)
        chainsaw.desenhar(tela)
        desenhar_barras()

        # Desenha a mensagem de pausa
        texto_pausa = fonte.render("PAUSADO", True, BRANCO)
        retangulo_pausa = texto_pausa.get_rect(center=(LARGURA // 2, ALTURA // 2))
        tela.blit(texto_pausa, retangulo_pausa)
        
        pygame.display.flip()

pygame.quit()
sys.exit()