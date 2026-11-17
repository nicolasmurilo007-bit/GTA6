# Teste 1: trailer oficial de GTA VI (análise)

Fonte: https://youtu.be/3JUboYgqIxc (Rockstar Games Brasil, 1 min 31 s).
Arquivo de trabalho: `videoplayback.mp4` no Google Drive do usuário
(id `1Nr3jZReSc1uzlBEBMvN31Bl6aKdQQdU4`), 640x360, 30 fps, 90,1 s, h264 + aac,
-13 LUFS. **O vídeo NÃO vai para o Git** (conteúdo da Rockstar; só teste privado).

Como obter o arquivo numa sessão nova: conector do Google Drive,
`download_file_content` com o id acima. Ele grava o arquivo em disco direto.

## Falas do trailer (Whisper small, inglês)
- 6,6-9,6 "Lucia, do you know why you're here?"
- 9,6-10,6 "Bad luck, I guess."
- 59,5-63,8 "We're gonna get through this."
- 64,8-66,8 "By sticking together." / 67,8-68,8 "Being a team."
- 68,8-76,7 "Trust?" ... "Trust."

## Cenas (41 cortes; instante em segundos)
- 0-2,7 aviso ESRB (descartar)
- 2,7-6,5 pôr do sol / cerca de arame (ambiente)
- 6,5-10,9 cena de presídio com Lucia
- 10,9 lancha vista de cima (esteira de espuma no mar)
- 18,4 prédios; 19,2 pântano ao entardecer; 21,7 praia lotada
- 23,3 lancha perto de navio de carga; 24,8 mulher sobre carro à noite
- 27,4 rua com lowriders; 29,0 boate; 30,0 close de dois homens
- 32,6 rua de Vice City com carros esportivos; 34,1 multidão em boate
- 35,7 aérea de ilhas e ponte; 37,4 piscina de cobertura; 39,8 letreiro VICE
- **41,3-59,5 "vídeos de rede social" dentro do jogo** (molduras de celular com
  @usuário, comentários e curtidas: 41,3; 43,9; 46,5; 49,9; 57,3), mais cenas
  de câmera de segurança/corporal (47,5; 48,6) e caos aéreo à noite (45,5)
- 59,5-62,5 carro por dentro; 62,5 Lucia dirigindo
- 63,6 telejornal "WEAZEL NEWS" com vista aérea de acidente; 64,6 distintivo
- 65,6 motos empinando na terra; 66,7 viaturas cercando cruzamento (aérea)
- 67,7 caminhonete com pessoas; 68,7 casal em loja; 70,3 carro derrapando na poeira
- 72,8 Lucia ao lado de abajur; 76,5 casal saindo de loja

## Proposta de 3 cortes (para o usuário aprovar)
Layout: o vídeo é 640x360, então 9:16 com recorte vertical ficaria ~202x360
(inutilizável). Usar vídeo centralizado sobre fundo desfocado. Em 1080p de fonte
o recorte vertical passa a servir.

| Corte | Intervalo | Duração | Assunto da narração |
|---|---|---|---|
| A (gancho) | 23,3-34,1 | 10,8 s | água da lancha + cidade viva (praia, rua, noite) |
| B | 41,3-52,1 | 10,8 s | trailer feito de vídeos de celular, "rede social" de Vice City |
| C | 59,5-72,8 | 13,3 s | fala original "We're gonna get through this" (59,5-63,8) + caos: motos, viaturas, carro derrapando |

Rascunho de roteiro (pt-BR, ~2,7 palavras/s; só afirma o que aparece na tela):
- A: "Repara na água dessa lancha: o casco abre o mar e deixa uma esteira de
  espuma. E a cidade em volta nunca para: praia cheia, ruas cheias, noite agitada."
- B: "Detalhe que quase ninguém notou: boa parte desse trailer é feita de vídeos
  de celular, com nome de usuário e comentários, como se Vice City tivesse a
  própria rede social."
- C: (fala original, legenda em português) depois: "No final, o caos: motos
  empinando na terra, viaturas fechando o cruzamento visto de cima, um carro
  derrapando na poeira. Quanta coisa ao mesmo tempo."

Custo estimado do ElevenLabs: ~16 créditos por segundo de fala; ~30 s de fala
= ~480 créditos (~US$ 0,10). Estimar de novo com `estimate_only` antes de gerar.

Aviso: afirmações sobre "física do jogo" que não aparecem na imagem precisam de
fonte confiável (informação oficial). Não inventar.
