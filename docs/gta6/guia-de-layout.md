# Guia de layout, gancho e legenda (regras medidas)

Fonte das regras: referências do projeto `pycodebr/heditor` (MIT, v2.21.0, 11/11/2026),
arquivos `references/captions-and-layout.md`, `quality-gates.md`, `hook-variants.md` e
`styles/reacao.md`, lidos em 18/11/2026. Nenhum código foi copiado; só as regras.
Também usado: o vídeo de referência do usuário (`estilo-referencia.md`).

## Zonas seguras em 1080x1920
- Topo 0-270 px: sem texto, rosto, logo ou gráfico importante (interface da plataforma).
  Títulos começam em y >= 300.
- Base: a partir de y ~1570 só atmosfera (a descrição e os botões do app ficam ali).
- Borda direita ~120 px entre y 1000-1700: botões de curtir/comentar/compartilhar.
- Rosto nunca coberto por legenda ou gráfico.

## Legenda
- Palavras ditas, em ordem, sincronizadas; correções de nome só no texto, sem mexer no tempo.
- Altura de letra >= 60 px no celular (usamos fonte 120 px, uma palavra por vez).
- Agrupar 1-3 palavras (<= 17 caracteres); nunca mais de 2 linhas.
- Contraste da palavra ativa: preto sobre amarelo claro `#ffd84d` ou branco, ou branco sobre
  cor escura saturada. Nunca texto escuro em pílula média nem contorno escuro em letra escura.
- Palavrão mascarado só na tela.

## Gancho
- Faixa de destaque no frame 0: 2-3 linhas, texto preto sobre amarelo, dizendo o que o
  criador fala no gancho; some na frase seguinte. Fica abaixo de y = 300.
- Gancho de teste A/B: muda só a abertura, o corpo fica idêntico (para medir de verdade).

## Layout
- "Herói": câmera grande entre y ~500 e 1200, banda de legenda logo abaixo (y 1222-1472),
  manchete acima (>= 300).
- Câmera pequena: ampliar para ~960 px de largura (Lanczos), nunca esticar na altura toda.
- Cortes de pausa viram troca de plano com zoom de ~1.0 <-> 1.075 no rosto; respiração de 1-2%.
- Estilo "reação" (indicado para streamer): ele em primeiro plano, a notícia/post ao fundo,
  com marcação na palavra certa.

## Portões de qualidade
- Volume final entre -15 e -13 LUFS, pico real <= -1,5 dBTP, correlação de áudio >= 0,99.
- Sem silêncio > 0,45 s dentro da fala; sem erro de decodificação.
- Margem do topo >= 270 px sem texto ou gráfico real.
- Tela "congelada" > 0,3 s só é erro se a imagem realmente travou.
- Conferir quadros do vídeo final (não só a prévia): elementos antigos que sobram são bug de tempo.

## O que o nosso pipeline já faz (render_video.py)
| Regra | Estado |
|---|---|
| Gancho em faixa amarela, y=400 | feito |
| Legenda de 1 palavra, 120 px, y=1270, "pop" | feito |
| Palavras-chave em amarelo (#ffd84d): números, `emphasis` do config, "!" e "?" | feito |
| -14 LUFS | feito (corte_01 ficou em -15,3, dentro de -15..-13 só no limite) |
| Zoom de 1.0<->1.075 nos cortes de pausa | NÃO feito |
| Câmera ampliada/recorte fechado no rosto | NÃO feito |
| Estilo "reação" com o post ao fundo | NÃO feito |
| Checagem automática de silêncio/topo/LUFS/pico | NÃO feita (agente `qualidade` faz por ffmpeg) |
