# Doutrina de movimento

Regras com número. Se uma decisão não está aqui, derive dos tokens de `src/lib/motion.ts`; não invente curva nova.

## Easing por comportamento

| Comportamento | Token | Curva |
|---|---|---|
| Entrar | `ease.enter` | bezier(0.16, 1, 0.3, 1) |
| Entrar seco (UI, texto curto) | `ease.sharp` | bezier(0.2, 0.75, 0.34, 0.94) |
| Assentar sem overshoot (zoom out, reveal) | `ease.settle` | bezier(0, 0.65, 0.51, 0.99) |
| Mudar de posição ou forma | `ease.move` | bezier(0.77, 0, 0.175, 1) |
| Sair | `ease.exit` | bezier(0.7, 0, 0.84, 0) |
| Rotação contínua, loop | `ease.linear` | linear |

| Herói da cena, chegada enfática | `easeX.emphasized` | bezier(0.05, 0.7, 0.1, 1) |
| Um overshoot só, no foco | `easeX.overshoot` | bezier(0.34, 1.56, 0.64, 1) |

Ease-in em entrada é erro. Bounce e elastic (oscilação de vários ciclos) são proibidos. Overshoot é um cruzamento só, de 3 a 8% além do alvo (`easeX.overshoot`, `springs.snappy` ou `springs.bouncy`), no elemento em foco, um por cena.

## Springs

`springs.smooth` (damping 200) para texto e câmera; `snappy` (damping 20, stiffness 200) para UI e ícones; `bouncy` só no foco; `heavy` para objetos grandes e logos. Spring precisa de `durationInFrames` quando a cena tem tempo fechado.

## Tempo

- Durações a 30 fps: micro 6 frames (200 ms), fast 10, base 16, slow 24. Entrada de vídeo até ~800 ms; saída cerca de 75% da entrada.
- Estrutura de cena: build 0 a 30%, breathe 30 a 70%, resolve 70 a 100%. A cena mais lenta dura cerca de 3x a mais rápida.
- Escala parte de 0,9 a 0,97 em UI; em vídeo pode partir de 0 com spring. Use `scale` e `translate`, nunca anime width, height, top ou left.
- Hierarquia: uma ação primária por batida, secundárias de até 30% da amplitude dela, ambiente de até 5%. Sobrepor secundária e primária é desejado; duas primárias ao mesmo tempo é erro.
- Hold: depois de cada chegada, 12 a 24 frames em que só o ambiente se mexe. `qa.py --timeline` avisa cena sem respiro.
- Sem quadro morto: em qualquer segundo, algo com significado está em andamento. Deriva sutil (`wiggle` com amplitude até 6 px) conta como vida, não como ação.
- Cascata: 1 a 3 frames por item, total até 500 ms; título longo aceita até 800 ms com `cascade()`.
- Princípios clássicos: antecipação curta antes de movimentos grandes, follow-through de 2 a 4 frames em partes soltas, movimento em arco, squash e stretch só em objetos elásticos.

## Cortes e transições

- Regra do olhar: o ponto de atenção do último frame de A é o ponto de entrada de B.
- Corte casado: mesmo eixo e direção dos dois lados, velocidade casada (saída acelera, entrada desacelera). O corte cai no meio do movimento.
- Deslocamento de whip em torno de 12% do quadro; blur de pico 10 a 14 px em texto, 18 a 20 px em superfícies.
- No máximo 2 ou 3 tipos de transição por vídeo. Fundo do root opaco para não piscar.
- `TransitionSeries` encurta a timeline: duas cenas de 60 frames com transição de 15 dão 105.

## Layout e tipografia

- Margem lateral de pelo menos 80 px em 1080 px de largura. Headline de 84 px ou mais em 1080p; legenda de 48 a 64 px.
- Safe area: ação em 90%, texto em 80%. 9:16: texto entre y 360 e 1420.
- Letter-spacing negativo leve (-0,02 em) em títulos grandes; peso 600 a 800 para títulos, 400 a 500 para corpo.
- Contraste WCAG AA. Sem gradiente linear de tela cheia em fundo escuro (banding); se usar, aplique grão.

## Legendas e leitura

- No máximo 2 linhas, 32 a 42 caracteres por linha, 0,5 s mínimo por bloco, 17 cps no máximo em pt-BR.
- Legenda e áudio no mesmo `Sequence`; tempos relativos ao arquivo de narração mais o `start` da partitura.

## Cor e estética

- Uma cor de acento; o resto em neutros com temperatura (papel quente, tinta escura). Acento marca a palavra falada, o objeto em foco ou o dado principal.
- Proibido: gradiente roxo-azul de tela cheia, glow genérico, tudo entrando com fade, tudo centralizado, ícones de banco de imagem sem tratamento, emoji.
