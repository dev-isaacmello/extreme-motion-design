# Técnicas avançadas: vocabulário de estúdio e como fazer em código

Leia a seção da técnica que for usar. Frames valem para 30 fps. Origem dos números: `[Carbon]` IBM Carbon motion e `[M3]` Material 3 (conferidos em 2026-10-09), `[Disney]` os 12 princípios (dão o conceito, não o número), `[prática]` consenso de estúdio sem fonte formal. Número `[prática]` é ponto de partida: confira no frame renderizado.

## Sumário

1. Princípios de animação aplicados
2. Tempo: cascata, rampa de velocidade, curvas
3. Cortes e transições
4. Máscaras, mattes e shape layers
5. Tipografia avançada
6. Expressões clássicas do After Effects em código
7. Procedural: ruído, campos e partículas
8. Look: grão, luz e lente
9. Câmera
10. UI, dados e logo
11. Remotion em 2026: o que há de novo

## 1. Princípios de animação aplicados

| Técnica | O que é | Números | Como fazer |
|---|---|---|---|
| Anticipation (antecipação) | recuo contrário antes da ação | 2 a 6 frames, 5 a 10% do percurso `[prática]` | `anticipate(frame, start, length, from, to, 0.08)` |
| Overshoot (ultrapassagem) | passa do alvo e assenta, um cruzamento só | 3 a 8% além, assenta em 4 a 8 frames `[prática]` | `easeX.overshoot` ou `springs.snappy`; só no elemento em foco |
| Follow-through (continuação) | partes soltas continuam depois que o corpo para | atraso de 2 a 4 frames, amplitude 10 a 30% `[Disney]` `[prática]` | filho usa `lag(frame, nível, 3)` na mesma função do pai |
| Overlapping action (ação sobreposta) | partes começam e terminam em tempos diferentes | 1 a 3 frames por nível da hierarquia | mesma curva com `lag` por profundidade |
| Secondary action (ação secundária) | movimento menor que apoia o principal | até 30% da amplitude da ação primária | camada própria; nunca cruza o ponto de atenção |
| Squash and stretch (achatar e esticar) | deforma preservando volume | 10 a 20% em estilo cartoon | `squash(0.15)` devolve `{sx, sy}`; `transformOrigin` no ponto de contato |
| Smear frame (borrão desenhado) | 1 ou 2 frames esticados no pico de velocidade | esticar 2 a 4x na direção do movimento | `scaleX(smear(velocity(fn, frame)))` |
| Arcos | trajetória curva, nunca reta entre dois pontos | flecha do arco de 5 a 15% da distância | progresso 0 a 1 lido com `getPointAtLength` de `@remotion/paths` |

Hierarquia de movimento em toda cena: uma ação **primária** por batida, **secundárias** de até 30% da amplitude e **ambiente** de até 5% (deriva com `wiggle`) para o quadro nunca morrer.

## 2. Tempo: cascata, rampa de velocidade, curvas

- **Offset, stagger, cascade (cascata)**: mesma animação defasada por item, 1 a 3 frames por item. Até 6 itens, `stagger(i, n, total)`. Lista longa: `cascade(i, n, total)` comprime os atrasos no fim para o último item não entrar depois que o olho saiu. Total de 300 a 500 ms em UI; título longo em vídeo aceita 600 a 800 ms `[prática]`.
- **Speed ramp, time remap (rampa de velocidade)**: o tempo acelera e freia dentro do plano, típico 400% para 25% para 100% com rampa de 6 a 12 frames. `const t = timeRemap(frame, [[0, 4], [12, 0.25], [40, 1]])` e passe `t` como frame para os filhos. Em vídeo real, lembre que desde o Remotion 4.0.530 `durationInFrames` é aplicado antes de `playbackRate`.
- **Value graph e speed graph (curva de valor e de velocidade)**: valor é a posição no tempo; velocidade é a derivada. Num ease-out forte, o pico de velocidade fica nos primeiros 20 a 30% do tempo. Confira com `velocity(fn, frame)`: salto de velocidade acima de 3x entre frames vizinhos fora de corte é tangente quebrada.
- **Curvas de referência**: expo out `(0.16, 1, 0.3, 1)` é o `ease.enter`. Decelerate enfático `(0.05, 0.7, 0.1, 1)` `[M3]` é o `easeX.emphasized`, para o herói da cena. Carbon: entrada expressiva `(0, 0, 0.3, 1)`, saída `(0.4, 0.14, 1, 1)`, durações 70, 110, 150, 240, 400 e 700 ms `[Carbon]`.
- **On twos, on threes (em dois, em três)**: `stepped(frame, 2)` dá 15 poses por segundo a 30 fps. Misture: personagem em twos, câmera contínua.
- **Hold**: todo movimento rápido pede 12 a 24 frames de respiro depois. Sem hold o olho não lê; `qa.py --timeline` mede isso.

## 3. Cortes e transições

| Técnica | O que é | Números | Como fazer |
|---|---|---|---|
| Match cut (corte por semelhança) | forma, posição e direção iguais dos dois lados | centro a até 5% do quadro | último frame de A e primeiro de B com mesmo centro e escala |
| Morph cut | a forma de A vira a forma de B | 8 a 16 frames | `morphPath` (flubber) ou `interpolatePaths` de `@remotion/paths` |
| Invisible cut (corte invisível) | corte escondido em whip, blur ou cor chapada | 2 a 4 frames de cobertura | corte no pico de velocidade do whip |
| Smash cut (corte seco) | corte abrupto entre intensidades opostas | sem transição; 2 a 4 frames de silêncio antes | `<Series>` sem transição e pausa no áudio |
| J-cut e L-cut | o som entra antes (J) ou continua depois (L) do corte | 4 a 12 frames | `<Sequence from>` do áudio defasado da imagem; em `timeline.json`, o `at` do SFX antes do `start` da cena |
| Wipe, iris, clock wipe | revelação por máscara | 10 a 20 frames | `wipe()`, `iris()`, `clockWipe()` de `@remotion/transitions`, ou `<IrisReveal progress>` |
| Shape transition (transição por forma) | uma forma cresce e vira o fundo da cena seguinte | 12 a 18 frames | `<IrisReveal>` com a cor da forma, partindo do objeto em foco (`cx`, `cy`) |
| Liquid transition (transição líquida) | borda orgânica que se funde | blur 10 a 20 px | `<GooeyFilter id="goo">` e `filter="url(#goo)"` no grupo |
| Light leak (vazamento de luz) | luz estourada cobrindo o corte | curto, uma vez | `lightLeak()` de `@remotion/effects/light-leak` em `<TransitionSeries.Overlay>` (pede WebGL2) |

Regra do olhar (eye trace): o ponto de atenção do último frame de A é o ponto de entrada de B. Se o foco muda de lugar, um movimento leva o olho até lá.

## 4. Máscaras, mattes e shape layers

- **Track matte alfa e luma**: uma camada define onde a outra aparece. Alfa: `clipPath` ou `mask-image`. Luma: `mask-mode: luminance` ou `<mask>` do SVG (branco mostra, preto esconde).
- **Trim paths**: `pathLength={1}` com `strokeDasharray={1}` e `strokeDashoffset` animado, ou `evolvePath` de `@remotion/paths`.
- **Repeater**: `Array.from({length: n})` com transform acumulado (rotação `i * 360 / n`, escala `0.9 ** i`) e atraso `lag(frame, i, 2)`.
- **Null e parenting**: `<g>` ou `<div>` aninhados; o null é o wrapper sem desenho que recebe o transform.
- **Anchor point (ponto de âncora)**: `transformOrigin`; em SVG, junto com `transformBox: 'fill-box'`.
- **Pre-comp**: `<Sequence>` aninhada reinicia o `useCurrentFrame()`; `<Freeze>` congela, `<Loop>` repete.
- **Limites reais**: offset path e merge paths não têm equivalente nativo em SVG. Offset aproximado com `strokeWidth` e `strokeLinejoin: 'round'`; booleana exata pede biblioteca (paper.js) ou desenhe a forma já pronta.

## 5. Tipografia avançada

- **Baseline reveal (subida por máscara)**: `<MaskReveal progress>` por palavra ou linha, com `lag(frame, i, 3)`. É a entrada padrão de estúdio; fade puro é o padrão de amador.
- **Range selector por caractere**: divida por grafema, atraso de 1 a 2 frames, 8 a 12 frames por caractere. Só em títulos de até 20 caracteres.
- **Tracking animado**: `letterSpacing` de `0.3em` para `0` em 20 a 30 frames; meça com `measureText` usando o mesmo `letterSpacing`.
- **Eixo de fonte variável**: `fontVariationSettings: "'wght' 300"` até `800` interpolado por frame, em fonte variável.
- **Texto que cabe**: `fitText`, `fitTextOnNLines` e `fillTextBox` de `@remotion/layout-utils`, medidos depois de a fonte carregar.
- **Contador (number ticker)**: `ticker(frame, start, 30, 0, valor)` com `fontVariantNumeric: 'tabular-nums'`; 20 a 45 frames e o valor final parado por 1 s ou mais.

## 6. Expressões clássicas do After Effects em código

| After Effects | Aqui |
|---|---|
| `wiggle(freq, amp)` | `wiggle(seed, frame, freq, amp)`; câmera na mão: 0,5 a 2 Hz, 2 a 6 px, 0,2 a 0,5 grau |
| `loopOut("cycle")` | `loopPhase(frame, period)` |
| `loopOut("pingpong")` | `pingPong(frame, period)` |
| `valueAtTime(time - delay)` (follow the leader) | `fn(lag(frame, i, 3))` |
| inertial bounce | um overshoot só: `easeX.overshoot`. Oscilação de vários ciclos continua proibida |
| `posterizeTime(12)` | `stepped(frame, fps / 12)` |

## 7. Procedural: ruído, campos e partículas

- **Flow field**: ângulo `noise3D(seed, x * s, y * s, t) * 2π` com `s` de 0,002 a 0,01. A posição de cada partícula é recalculada desde o frame 0 a cada render; nunca guarde estado acumulado em `useRef`.
- **Partículas**: forma fechada `p0 + v * t + 0.5 * g * t²` com `random(seed + i)` para posição e velocidade iniciais.
- **Turbulent displace**: `feTurbulence` com `baseFrequency` de 0,01 a 0,05 mais `feDisplacementMap` com `scale` de 10 a 40. `<BoilFilter>` é o caso em degraus.
- **Eco, trails**: `<Echo copies={4} lag={2} render={(f) => ...} />` desenha cópias atrasadas; some com `smear` no pico.

## 8. Look: grão, luz e lente

| Efeito | Números `[prática]` | Como fazer |
|---|---|---|
| Grão | opacidade 4 a 10% | `<Grain>` por cima de tudo |
| Halation | blur de 1 a 2% da largura, 15 a 30% de opacidade | cópia das altas luzes com blur, tinta laranja, `mixBlendMode: 'screen'` |
| Aberração cromática | 1 a 3 px em 1080p; acima disso denuncia | canais separados com `feColorMatrix` e `feOffset` |
| Bloom | 2 ou 3 passes de blur | cópia com limiar, blur e `screen` |
| Profundidade de campo | 0 no foco, 8 a 20 px no fundo | `filter: blur()` por `<Layer>` conforme a profundidade |
| Varredura de luz (shine) | 12 a 20 frames, uma vez, faixa de 15 a 25% | `<Shine progress>` no logo ou no dado principal |
| Sombra e luz 2D | uma direção de luz fixa na cena | gradiente, sombra interna e rim light na mesma máscara |
| Isométrico | `rotateX(54.7deg) rotateZ(45deg)` | eixos a 30 graus, escala vertical 0,816 |

Cada efeito de lente entra uma vez e com motivo. Grão, aberração e glow juntos em tudo é assinatura de gerado.

## 9. Câmera

- Anime a câmera, não os objetos: um easing no `<Camera>` move tudo em coerência; objeto só recebe movimento local.
- Câmera e objeto nunca animam o mesmo eixo ao mesmo tempo.
- Overshoot de câmera: passa 1 a 3% do alvo e assenta em 6 a 10 frames, só em chegada de impacto.
- Parallax: fundo com fator 0,2 a 0,5 e primeiro plano 1,2 a 1,5 (`<Layer depth>` de 2 a 5 e de 0,7 a 0,85).

## 10. UI, dados e logo

- **Shared element, container transform**: o mesmo elemento interpola do retângulo A para o B e o conteúdo faz crossfade no meio; calcule os dois retângulos e interpole direto (é o FLIP sem medir o DOM).
- **Lista em cascata**: 1 a 2 frames por item, só nos 6 a 8 primeiros.
- **Skeleton**: shimmer em loop de 1,2 a 1,5 s e crossfade de 150 a 240 ms para o conteúdo.
- **Coreografia de cursor**: arco com `ease.move`, pausa de 4 a 8 frames antes do clique, clique com escala 0,9 por 3 a 4 frames, resposta da UI 1 a 2 frames depois.
- **Dados**: eixos, depois marcas, depois rótulos. Barra cresce da linha de base, linha se desenha, valor final legível por 1 s ou mais.
- **Logo sting**: quatro fases em 2 a 5 s: construção (40 a 60%), resolução (10 a 15%), hold (25 a 35%) e assinatura. O impacto do áudio cai no frame da resolução.

## 11. Remotion em 2026: o que há de novo

Conferido em remotion.dev em 2026-10-09; o template fixa a versão 4.0.534. Remotion 5.0 não foi lançado.

- `@remotion/transitions`: `fade`, `slide`, `wipe`, `flip`, `clockWipe`, `iris`, `none`; `<TransitionSeries.Overlay>` não muda a duração. Transição e overlay não podem ser vizinhos.
- `@remotion/motion-blur`: `<CameraMotionBlur shutterAngle samples>` e `<Trail>`.
- `@remotion/effects`: prop `effects` com `blur()`, `lut()` e `lightLeak()`; `createEffect()` para efeito próprio. Não está no template: instale com a mesma versão exata.
- `@remotion/paths`: `interpolatePaths()` para morph entre paths compatíveis.
- `@remotion/captions`: `createTikTokStyleCaptions` para legenda por página.
- `@remotion/media-parser` e `@remotion/webcodecs` estão descontinuados em favor do Mediabunny.
- Licença: grátis para indivíduo e empresa de até 3 pessoas. A partir de 4, Company License (US$ 25 por mês por pessoa que escreve código Remotion; render automatizado tem preço próprio).
