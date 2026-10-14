# QA, lint, dailies e entrega

## Lint antes do render (`lint.py`, bloqueante em FAIL)

`python3 <skill>/scripts/lint.py` na pasta do projeto lê `public/timeline.json`, o `words.json` da narração e `src/`. Roda em menos de 1 s, então rode a cada mudança de partitura ou de cena.

| Verificação | Nível |
|---|---|
| Projeto sem `direction.json`, contrato incompleto, cena sem layout, entrada e herói declarados | FAIL |
| Todas as cenas com o mesmo layout ou a mesma entrada | FAIL |
| Cenas vizinhas com o mesmo par layout e entrada; direção escolhida pelo agente | WARN |
| Cenas com buraco, sobreposição ou fora da duração | FAIL |
| Corte dentro de uma palavra falada; voz que termina depois do vídeo | FAIL |
| SFX fora da duração | FAIL |
| `Math.random`, relógio de parede, timers, `useFrame`, transição ou animação CSS, `Easing.bounce` e `Easing.elastic` | FAIL |
| Corte que não casa com início de frase (tolerância de 0,25 s) | WARN |
| Cena acima de 2,6 palavras por segundo; cena com menos de 1 s | WARN |
| Todas as cenas com a mesma duração | WARN |
| Dois SFX a menos de 0,12 s; menos de 1 s de quadro final depois da última palavra | WARN |
| `interpolate(frame, ...)` sem `easing`; curva criada fora de `lib/motion.ts`; cor escrita fora de `theme.ts` | WARN |
| Tag HTML de mídia; emoji; muito mais `opacity` que transform | WARN |

WARN é heurística: leia, decida e diga na entrega o que ficou.

## Dailies (antes do render final, obrigatório)

1. Stills em lote: `node <skill>/scripts/stills.cjs Showcase` na pasta do projeto renderiza início, meio e fim de cada cena com um bundle e um browser só (21 frames em cerca de 7 s; a CLI leva 3 a 4 s por frame porque refaz os dois a cada chamada). Grava em `out/stills`.
2. `uv run <skill>/scripts/layout.py out/stills --timeline public/timeline.json` mede o texto de cada still (tabela abaixo). Corrija os FAIL antes de olhar a folha.
3. `contact_sheet.py --stills out/stills -o out/sheet.png` monta a folha sem MP4.
4. Abra a imagem e responda PASS ou FIX por quadro. Depois dos seus FIX, a folha vai para o revisor independente (`references/critic.md`).
5. Quando um feedback citar um momento, renderize aquele instante (`stills.cjs Showcase --times 12.4,12.6 --scale 1 --out out/sf`) e olhe antes de editar.
6. Draft em vídeo (`node <skill>/scripts/render.cjs Showcase --draft`, meia escala, fora do orçamento) só quando o que está em dúvida é movimento ou ritmo: rode o `qa.py --timeline` em `out/draft.mp4`.
7. Outro formato: `stills.cjs Showcase --format reels --out out/stills-reels` e `layout.py out/stills-reels`. Cada formato tem a sua área segura.

Rodada em que só a voz mudou não pede folha nova: o usuário ouve `public/audio/mix.wav`.

## Layout medido (`layout.py`, bloqueante em FAIL)

A composição carrega a sonda `<Probe />`. Quando o `stills.cjs` pede um frame, ela mede no DOM cada texto (caixa, tamanho real depois dos transforms, cor, opacidade, quanto está escondido por máscara) e o script lê a cor de fundo nos pixels do PNG. Só texto assentado é julgado: palavra no meio de uma entrada não conta.

| Verificação | Nível |
|---|---|
| Texto cortado pela borda do quadro | FAIL |
| Texto fora da área de ação (90% do quadro) | FAIL |
| Dois textos sobrepostos (mais de 15% da caixa menor) | FAIL |
| Letra menor que 20 px no lado menor de 1080 | FAIL |
| Contraste abaixo de 3:1 contra o fundo medido | FAIL |
| Texto fora da área segura de texto (80%; em 9:16, y 360 a 1420) | WARN |
| Letra entre 20 e 28 px; contraste entre 3:1 e 4,5:1 em letra menor que 40 px | WARN |
| Cenas vizinhas com semelhança acima de 0,90, ou mediana da peça acima de 0,80 (`--timeline`) | WARN |

- Texto ornamental que sangra do quadro de propósito leva o atributo `data-decor` e fica fora da medição.
- Limites: texto desenhado em canvas, em WebGL ou dentro de imagem não está no DOM e não é medido. A sonda não sabe o que está por cima: texto coberto por outra camada opaca (uma transição que tapa a cena) é medido como se estivesse visível e reprova por contraste; faça a cena sair antes de ser coberta. Uma linha de texto é medida numa faixa de 1,2 em em volta do meio da caixa, porque a caixa do DOM tem a altura da área de conteúdo da fonte (até 1,5 em numa condensada) e não a do glifo. Texto que cresce por escala só é julgado no still em que atinge o tamanho maior. Fundo de foto ou gradiente dá contraste aproximado (a mensagem diz "fundo irregular"). A semelhança entre cenas compara miniaturas em cinza de 24x24; nos quatro vídeos reais usados na calibração a mediana ficou entre -0,08 e 0,29 e o maior par em 0,73, e não havia amostra de vídeo repetitivo, então o limiar é conservador.

## Direção medida (`design.py`, aviso)

`uv run <skill>/scripts/design.py out/stills --timeline public/timeline.json` mede um still por cena e conta os sinais do quadro que o modelo faz sem direção nenhuma (lista e antídotos em `design.md`, seção 9):

| Sinal | Como é medido |
|---|---|
| quase preto com um acento | fundo com L abaixo de 0,25 e no máximo uma cor saturada, em 60% dos quadros ou mais |
| duas cores | só duas cores com 2% da área ou mais, em 60% dos quadros ou mais |
| mesma composição | o centro da massa visual quase não muda entre cenas (dispersão abaixo de 0,05) |
| condensada gigante | o maior texto é uma condensada em 60% dos quadros ou mais |
| tudo em caixa alta | mais da metade dos blocos de texto em caixa alta |
| mono de enfeite | texto mono em 60% dos quadros ou mais e acima de 15% dos blocos |
| tudo na margem esquerda | o maior texto começa na margem esquerda em 70% dos quadros ou mais |
| peso único | o maior texto é pesado em 90% dos quadros ou mais |

Três sinais ou mais dão o veredito "padrão do modelo"; dois, "perto do padrão". Calibração da 2.0.0: o exemplo do template dá 3 sinais e um reel maximalista feito com a 1.3 dá 4, os dois corretamente como padrão. `--video arquivo.mp4` mede só pixels de qualquer vídeo, sem os sinais de texto. Em peça sobre filmagem, "mesma composição" e área vazia não dizem nada: o quadro é o da câmera.

## Checklist visual

- Algum texto cortado, fora da safe area ou sobre o sujeito?
- O primeiro frame de cada cena já tem algo legível ou está vazio?
- Há duas ações competindo no mesmo momento?
- A palavra em destaque coincide com a palavra falada?
- Cores fora da paleta, gradiente roxo, glow, tudo centralizado?
- Contraste suficiente em todos os textos?
- Algo pisca branco ou preto no corte?
- O último frame fecha a ideia (logo, CTA ou frase final segura por pelo menos 1 s)?

## Gate automático (`qa.py`, bloqueante)

| Verificação | Regra |
|---|---|
| Codec | h264 e yuv420p (faixa TV). `yuvj420p` reprova: rode `deliver.py` |
| Contraste (`--stills`) | frames do MP4 comparados aos stills da mesma composição: erro médio até 5/255 e preto e branco a até 6/255 do still. Reprova faixa de luma comprimida por reencode |
| Áudio | AAC presente e duração igual à do vídeo (até 0,15 s) |
| Loudness | alvo do perfil até 1 LU; true peak até o máximo do perfil |
| Flashes | no máximo 3 por segundo (aproximação da WCAG 2.3.1) |
| Pop de 1 frame (aviso) | um quadro diferente dos dois vizinhos, que são iguais entre si |
| Emenda de loop (`--loop`) | diferença entre último e primeiro frame no nível de um passo normal |
| Avisos | cor sem marca BT.709, resolução do perfil, fps padrão, trecho parado acima de 1,5 s, frames pretos, leitura acima de 17 cps |
| Ritmo (`--timeline`) | por cena: energia de movimento, fração do tempo em respiro, maior respiro e posição do pico. Avisa cena sem respiro de 0,25 s, cena quase toda parada e peça sem contraste (cena mais agitada abaixo de 1,5x a mais calma) |

O medidor de ritmo é um medidor, não um juiz: os limiares foram ajustados em um único vídeo real e servem para apontar onde olhar na folha de contato.

## Render por cena, formatos e orçamento (`render.cjs`)

- `node <skill>/scripts/render.cjs Showcase` renderiza cada cena da partitura como um trecho (um bundle e um browser para todas) e emenda sem reencode com o áudio de `timeline.audio`. Medido no vídeo do template: 12,7 s contra 11,8 s do `remotion render` inteiro, SSIM 0,9998 entre os dois.
- `--scene fecho` refaz só aquela cena e reaproveita os outros trechos (6,2 s no mesmo vídeo). Se a partitura mudou o intervalo de outra cena, ela é refeita junto. Mudou tema, componente ou bloco que várias cenas usam: rode sem `--scene`, o remendo só sabe o que você disse que mudou.
- `--formats reels,square,youtube` entrega os três numa rodada, com a mesma composição (`useFormat()` nas cenas). Cada formato passa pelo seu `stills.cjs --format` e pelo `layout.py` antes.
- `--remux` remonta o master com o `mix.wav` novo sem renderizar nenhuma cena: é o caminho quando só trilha, voz ou SFX mudaram e a duração das cenas ficou igual.
- O áudio entra em AAC com um limitador 1 dB abaixo do teto do mix: sem ele o AAC devolveu pico de -0,8 dBTP para um WAV em -2,8.
- `--draft` renderiza em meia escala em `out/draft.mp4` e não conta no orçamento.
- **Orçamento**: `budget` na partitura (`full_renders` 4 e `stills` 30 por chamada, por padrão; mude no `roteiro.json`). No quinto render completo o script recusa e pede `--over "motivo"`. Cada chamada de `stills.cjs` e de `render.cjs` fica em `out/ledger.json`. O teto existe porque disciplina de custo escrita em prosa não segura: conferir no still custa segundos, conferir no render custa minutos e cota.

## Entrega

- Renderize com `--color-space=bt709` (o `remotion.config.ts` do template já define): o MP4 sai h264 yuv420p faixa TV, marcado BT.709, com AAC 48 kHz e faststart.
- `deliver.py` confere isso e copia o vídeo sem reencode. Só reencoda (CRF 18) quando a origem chega em faixa cheia (`yuvj420p`) ou em outro pixel format. Comprimir a faixa de um arquivo que já está em faixa TV lava o contraste: preto vira cinza e o branco perde brilho.
- Perfis: `youtube` 1920x1080, `reels` e `tiktok` 1080x1920, `square` 1080x1080, `linkedin` 1920x1080.
- Entregue: `final.mp4`, `sheet.png` e o texto de créditos (campo `attribution` de cada item do `credits.json`, mais "made using Openverse" quando houver).
- Diga na entrega, sem suavizar: o que ficou em WARN, quem aprovou a direção, se houve revisor independente, quantos renders completos foram gastos (`out/ledger.json`) e todo recurso que caiu em alternativa (voz paga que virou local, trilha gerada no lugar de faixa, formato diferente do pedido, cena simplificada). Vídeo que passa no gate com um recurso degradado e não avisa é defeito de entrega.

## Setup e problemas comuns

- Chrome: o Remotion baixa o Chrome Headless Shell na primeira renderização. Em rede restrita, aponte um Chromium local com `--browser-executable=<caminho>`.
- Fontes: `@remotion/google-fonts` baixa a fonte no render; sem rede, use fonte local com `@remotion/fonts` e `staticFile`.
- Render lento: use a flag que o `gl.py` devolve. Ele renderiza um trecho com o backend padrão, `vulkan` e `angle-egl`, e só troca o padrão por um que seja ao menos 20% mais rápido com SSIM de 0,99 ou mais; guarda em `out/gl.json` (`--force` mede de novo). Não fixe `--gl=vulkan` à mão: sem GPU ele roda em software sem avisar e pode dobrar o tempo. `--frames=0-60` testa trechos.
- Filtro SVG de tela cheia com seed por frame (o `<Grain>`) custa de 13% a 20% do render e, no backend padrão, impede o ganho de `--concurrency`: com ele ligado, 4, 6 e 8 abas levam o mesmo tempo. Motion blur também custa caro.
- 3D sem GPU: `--gl=swangle`.
