import os
import pygame
import threading
import time
import random
from io import BytesIO
from gtts import gTTS
from openai import OpenAI

# Inicializa o mixer com definições seguras para o Raspberry Pi
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()
pygame.font.init()
pygame.mixer.init()

# CONFIGURAÇÃO DE TELA (Fullscreen)
info = pygame.display.Info()
LARGURA, ALTURA = info.current_w, info.current_h
tela = pygame.display.set_mode((LARGURA, ALTURA), pygame.FULLSCREEN)
pygame.display.set_caption("Assistente 001 - Baymax Vermelho")

# Cores
VERMELHO = (200, 0, 0)
VERMELHO_CLARO = (255, 60, 60)
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
CINZA = (60, 60, 60)
FUNDO = (15, 15, 20)
CINZA_TEXTO_LABEL = (180, 180, 180) 
AZUL_ESCURO_CUBE = (25, 40, 50) # Cor do cubo da logo na testa

# Fontes (Usando SysFont para compatibilidade)
fonte = pygame.font.SysFont("Arial", 36)
fonte_pequena = pygame.font.SysFont("Arial", 28)

# Carrega a logo do FabLab (Certifique-se de que "fablab_logo.png" está na pasta)
LOGO_FILENAME = "fablab_logo.png"
logo_fablab = None
try:
    if os.path.exists(LOGO_FILENAME):
        logo_original = pygame.image.load(LOGO_FILENAME).convert_alpha()
        l_altura = int(ALTURA * 0.15)
        l_largura = int(logo_original.get_width() * (l_altura / logo_original.get_height()))
        logo_fablab = pygame.transform.scale(logo_original, (l_largura, l_altura))
    else:
        print(f"Aviso: {LOGO_FILENAME} não encontrado.")
except Exception as e:
    print(f"Erro ao carregar imagem: {e}")

# Estado global
falando = False
texto_input = ""
resposta = ""
rodando = True
olhos_fechados = False
ultimo_piscar = time.time()
duracao_piscar = 0.12


def falar(texto):
    """Gera voz a partir de texto e reproduz."""
    global falando
    try:
        falando = True
        tts = gTTS(texto, lang="pt")
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)

        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    except Exception as e:
        print("Erro no TTS:", e)
    finally:
        falando = False

def quebrar_texto(texto, fonte_obj, largura_max):
    """Quebra o texto em várias linhas para caber na caixa."""
    palavras = texto.split(" ")
    linhas = []
    linha_atual = ""
    for palavra in palavras:
        teste = linha_atual + palavra + " "
        if fonte_obj.size(teste)[0] <= largura_max - 40:
            linha_atual = teste
        else:
            linhas.append(linha_atual.strip())
            linha_atual = palavra + " "
    if linha_atual:
        linhas.append(linha_atual.strip())
    return linhas


def desenhar_rosto():
    tela.fill(FUNDO)
    
    # Centro e Raio da Cabeça
    raio = int(min(LARGURA, ALTURA) * 0.18)
    cx = LARGURA // 2
    logo_y_pos = int(ALTURA * 0.05)
    
    # Define a altura da cabeça com base na logo
    if logo_fablab:
        cy = logo_y_pos + logo_fablab.get_height() + int(ALTURA * 0.03) + raio
    else:
        cy = int(ALTURA * 0.35)

    # 1. Desenha Logo no Topo
    if logo_fablab:
        lx = (LARGURA - logo_fablab.get_width()) // 2
        tela.blit(logo_fablab, (lx, logo_y_pos))

    # 2. Desenha Cabeça (Círculo)
    cor_cabeca = VERMELHO_CLARO if falando else VERMELHO
    pygame.draw.circle(tela, cor_cabeca, (int(cx), int(cy)), int(raio))

    # 3. Desenha Cubo na Testa
    cube_size = int(raio * 0.25)
    cube_x = cx - cube_size // 2
    cube_y = cy - raio + int(raio * 0.15)
    pygame.draw.rect(tela, AZUL_ESCURO_CUBE, (int(cube_x), int(cube_y), cube_size, cube_size))

    # 4. Desenha Olhos
    olho_r = int(raio * 0.12)
    dist_o = int(raio * 0.9)
    ox1, ox2 = cx - dist_o // 2, cx + dist_o // 2
    oy = cy

    if olhos_fechados:
        # Olho fechado (linha)
        pygame.draw.line(tela, PRETO, (int(ox1 - olho_r), int(oy)), (int(ox1 + olho_r), int(oy)), 6)
        pygame.draw.line(tela, PRETO, (int(ox2 - olho_r), int(oy)), (int(ox2 + olho_r), int(oy)), 6)
    else:
        # Olho aberto (círculo)
        brilho = 255 if falando else 120
        cor_olho = (brilho, brilho, brilho)
        pygame.draw.circle(tela, cor_olho, (int(ox1), int(oy)), int(olho_r))
        pygame.draw.circle(tela, cor_olho, (int(ox2), int(oy)), int(olho_r))

    # Conector entre os olhos
    pygame.draw.line(tela, PRETO, (int(ox1 + olho_r), int(oy)), (int(ox2 - olho_r), int(oy)), 6)

    # 5. Desenha Boca (Pontos quando fala)
    if falando:
        for i in range(random.randint(2, 5)):
            px = cx - 40 + (i * 20)
            py = cy + int(raio * 0.6)
            pygame.draw.circle(tela, BRANCO, (int(px), int(py)), 5)

    c_w = int(LARGURA * 0.8)
    c_h = int(ALTURA * 0.12)
    c_x = (LARGURA - c_w) // 2

    py_box = int(ALTURA * 0.65)
    pygame.draw.rect(tela, VERMELHO, (c_x, py_box, c_w, c_h))
    pygame.draw.rect(tela, BRANCO, (c_x, py_box, c_w, c_h), 3)
    
    label_p = fonte_pequena.render("Pergunta:", True, CINZA_TEXTO_LABEL)
    tela.blit(label_p, (c_x, py_box - 35))
    
    txt_input_wrap = quebrar_texto(texto_input, fonte, c_w)
    for i, linha in enumerate(txt_input_wrap[-1:]): # Apenas a última linha digitada
        img_p = fonte.render(linha, True, BRANCO)
        tela.blit(img_p, (c_x + 20, py_box + 15))

    # Caixa Resposta
    ry_box = int(ALTURA * 0.82)
    pygame.draw.rect(tela, VERMELHO, (c_x, ry_box, c_w, c_h))
    pygame.draw.rect(tela, BRANCO, (c_x, ry_box, c_w, c_h), 3)
    
    label_r = fonte_pequena.render("Resposta:", True, CINZA_TEXTO_LABEL)
    tela.blit(label_r, (c_x, ry_box - 35))

    if resposta:
        resp_wrap = quebrar_texto(resposta, fonte_pequena, c_w)
        for i, linha in enumerate(resp_wrap[:3]): # Mostra as primeiras 3 linhas
            img_r = fonte_pequena.render(linha, True, BRANCO)
            tela.blit(img_r, (c_x + 20, ry_box + 10 + (i * 30)))

    pygame.display.flip()

CHAVE_API = "COLE_SUA_CHAVE_AQUI"
cliente = OpenAI(api_key=CHAVE_API)

def gerar_resposta(pergunta):
    global resposta
    resposta = "A pensar..."
    try:
        r = cliente.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "És o Assistente 001 do FabLab Livre SP. Simpático como o Baymax. Respostas curtas."},
                {"role": "user", "content": pergunta}
            ],
            max_tokens=100
        )
        resposta = r.choices[0].message.content.strip()
        threading.Thread(target=falar, args=(resposta,), daemon=True).start()
    except Exception as e:
        resposta = f"Erro: {str(e).splitlines()[0]}"


clock = pygame.time.Clock()

while rodando:
    agora = time.time()
    
    # Lógica de piscar olhos
    if not falando:
        if not olhos_fechados and agora - ultimo_piscar > random.uniform(3, 6):
            olhos_fechados = True
            ultimo_piscar = agora
        elif olhos_fechados and agora - ultimo_piscar > duracao_piscar:
            olhos_fechados = False

    desenhar_rosto()

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                rodando = False
            elif evento.key == pygame.K_RETURN:
                if texto_input.strip() and not falando:
                    p = texto_input.strip()
                    texto_input = ""
                    threading.Thread(target=gerar_resposta, args=(p,), daemon=True).start()
            elif evento.key == pygame.K_BACKSPACE:
                texto_input = texto_input[:-1]
            else:
                if not falando:
                    texto_input += evento.unicode

    clock.tick(30)

pygame.quit()