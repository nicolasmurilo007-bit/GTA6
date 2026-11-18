# Gancho: 2026-11-18_alanzoka_que-isso-rockstar

Base verificada no clipe (30 s, gameplay de GTA 6 no clipe de espectador do Alanzoka): uma NPC de biquini, chapeu e cachorrinho fala coisas estranhas ao Jason (dialogo na legenda do jogo); o Alan (camera no canto direito) cai na risada. A punchline dele (~18-21 s) nao e revelada em nenhuma opcao.
Sem gancho anterior em `runs/*/gancho.md` (nenhum encontrado), entao nao ha repeticao.
Sem emoji (a fonte do video nao renderiza). Linhas de ate 20 caracteres, faixa amarela com texto preto, primeiros ~3,5 s, abaixo de y=300.

## Opcao A (melhor)

Gancho (12 palavras): Que NPC é essa do GTA 6? Espera a reação do Alan

Texto de `hook` (4 linhas):

```
QUE NPC É ESSA
DO GTA 6?
ESPERA A REAÇÃO
DO ALAN
```

Texto curto para a tela (<= 5 palavras): ESPERA A REAÇÃO DO ALAN

Por que: pergunta curiosa + promessa de pagamento (padrao aprovado); a promessa (reacao do Alan) acontece de fato; nao entrega a frase final.

## Opcao B

Gancho (10 palavras): Será que o Alan aguenta essa NPC? Assiste até o fim

```
SERÁ QUE O ALAN
AGUENTA ESSA NPC?
ASSISTE ATÉ O FIM
```

Texto curto para a tela: SERÁ QUE ELE AGUENTA?

Por que: formato mais proximo do exemplo aprovado ("sera que... assiste ate o final"); o Alan de fato cai na risada, entao nao e enganoso.

## Opcao C

Gancho (10 palavras): O diálogo dessa NPC quebrou o Alan. Assiste até o fim

```
O DIÁLOGO DESSA NPC
QUEBROU O ALAN.
ASSISTE ATÉ O FIM
```

Texto curto para a tela: NPC QUEBROU O ALAN

Por que: afirmacao em vez de pergunta (variacao para o teste A/B); "quebrou" = ele ri sem parar, verdadeiro e sem revelar a frase.

## Teste A/B

Mudar SO o `hook` do config e manter o corpo identico; nomear as saidas com sufixo `-abA`, `-abB`, `-abC`.
