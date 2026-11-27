# Gancho: 2026-11-27_alanzoka_trabalhadores

Base verificada no clipe (60 s; contexto.json + frames/): o Alan briga numa garagem, os trabalhadores de colete se juntam contra ele (13-15 s: "os trabalhadores se juntaram contra mim!"), ele grita por polícia e socorro, diz "a revolta dos trabalhadores" (22-24 s), "abre o portão" (35-37 s), quebra a janela (45 s) e foge de carro (53-58 s). Quadro de 48,75 s: o grupo de colete cerca o carro vermelho. A fuga não é revelada em nenhuma opção.
Ganchos anteriores (não repetir): "Que NPC é essa do GTA 6? Espera a reação do Alan" (18/11), "Roubou na frente da polícia? E o plano do Alan..." (20/11), "O Cellbit achou o Pé Grande... e virou SAPO?" (21/11). Aqui não se usa "espera a reação", "e o plano do Alan..." nem "na frente da polícia".
Sem emoji (a fonte não renderiza). Layout empilhado: câmera do Alan até y=668, então `hook_y` = 700; até 3 linhas de no máximo 20 caracteres; faixa amarela, texto preto; `hook_seconds` = 3.5.
Atenção à legenda: "foda-se" em 45,4-46,0 s (o gancho não tem palavrão; decidir se a legenda censura).

## Opção A (melhor)

Gancho (6 palavras): Revolta dos trabalhadores! O Alan escapa?

Texto de `hook` (3 linhas):

```
REVOLTA DOS
TRABALHADORES!
O ALAN ESCAPA?
```

Texto curto para a tela (até 5 palavras): O ALAN ESCAPA?

Por quê: usa a fala do próprio Alan ("a revolta dos trabalhadores"), que é literal no clipe; a pergunta é a promessa de pagamento (o espectador fica até ver a fuga) sem contar como ele sai.

## Opção B

Gancho (7 palavras): Os trabalhadores se juntaram contra o Alan...

```
OS TRABALHADORES
SE JUNTARAM
CONTRA O ALAN...
```

Texto curto para a tela: TODOS CONTRA O ALAN

Por quê: frase quase literal dele (13-15 s); as reticências seguram o desfecho. Mais descritiva, menos pergunta.

## Opção C

Gancho (8 palavras): Mexeu com os trabalhadores errados. Assiste até o fim

```
MEXEU COM OS
TRABALHADORES ERRADOS
ASSISTE ATÉ O FIM
```

Texto curto para a tela: MEXEU COM OS ERRADOS

Por quê: tom de meme; é verdade (ele começa a confusão e o grupo reage). "TRABALHADORES ERRADOS" tem 21 caracteres: encurtar para "OS ERRADOS" se a linha estourar.

## Teste A/B

Mudar SÓ o `hook` em `clipe.json` (manter `hook_y` = 700, `hook_seconds` = 3.5 e o corpo idêntico); nomear as saídas com sufixo `-abA`, `-abB`, `-abC`.
