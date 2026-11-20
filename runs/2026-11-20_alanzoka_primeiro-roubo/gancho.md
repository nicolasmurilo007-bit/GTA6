# Gancho: 2026-11-20_alanzoka_primeiro-roubo

Base verificada no clipe (30 s; contexto.json + quadros): primeiro assalto da Lucia numa loja; um homem cai no chão (~5 s), ela foge com a bolsa rosa e passa por policiais (~17 s). O Alan diz "ela roubou bem com a polícia na frente" (17-19 s) e depois promete zerar o jogo "sem matar ninguém, 100% good ending" (22-25 s). A promessa não é revelada nas opções A e B.
Ganchos anteriores (`runs/2026-11-18_alanzoka_que-isso-rockstar/gancho.md`): "Que NPC é essa do GTA 6? Espera a reação do Alan" e variantes. Aqui não se repete "espera a reação" nem "quebrou o Alan".
Sem emoji (a fonte do vídeo não renderiza). Layout empilhado: câmera do Alan até y=668, então `hook_y` = 700, até 3 linhas de no máximo 20 caracteres, faixa amarela com texto preto, primeiros 3,5 s.

## Opção A (melhor)

Gancho (10 palavras): Roubou na frente da polícia? E o plano do Alan...

Texto de `hook` (3 linhas):

```
ROUBOU NA FRENTE
DA POLÍCIA?
E O PLANO DO ALAN...
```

Texto curto para a tela (até 5 palavras): ROUBOU NA FRENTE DA POLÍCIA?

Por quê: pergunta curiosa + promessa de pagamento (padrão aprovado). As duas coisas acontecem: ela passa pelos policiais com a bolsa e o Alan anuncia o plano em 22-25 s. As reticências seguram a promessa dele sem revelar.

## Opção B

Gancho (8 palavras): 1º assalto da Lucia. Espera a promessa do Alan

```
1º ASSALTO DA LUCIA
ESPERA A PROMESSA
DO ALAN
```

Texto curto para a tela: ESPERA A PROMESSA DO ALAN

Por quê: afirmação + promessa de pagamento; deixa clara a novidade (primeira missão de roubo da Lucia). "Promessa" é literal: ele promete zerar sem matar ninguém.

## Opção C

Gancho (10 palavras): Zerar o GTA 6 sem matar ninguém? O Alan vai tentar

```
ZERAR O GTA 6
SEM MATAR NINGUÉM?
O ALAN VAI TENTAR
```

Texto curto para a tela: SEM MATAR NINGUÉM?

Por quê: pergunta mais forte e polêmica (gera comentário), mas entrega antes a fala principal do Alan (22 s). É verdade (ele diz que vai tentar), só que a cena perde a surpresa. Bom para o teste A/B.

## Teste A/B

Mudar SÓ o `hook` em `clipe.json` (manter `hook_y` = 700 e o corpo idêntico); nomear as saídas com sufixo `-abA`, `-abB`, `-abC`.
