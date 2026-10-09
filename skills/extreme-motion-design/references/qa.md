# QA, lint, dailies e entrega

## Lint antes do render (`lint.py`, bloqueante em FAIL)

`python3 <skill>/scripts/lint.py` na pasta do projeto lê `public/timeline.json`, o `words.json` da narração e `src/`. Roda em menos de 1 s, então rode a cada mudança de partitura ou de cena.

| Verificação | Nível |
|---|---|
| Cenas com buraco, sobreposição ou fora da duração | FAIL |
| Corte dentro de uma palavra falada; voz que termina depois do vídeo | FAIL |
| SFX fora da duração | FAIL |
| `Math.random`, relógio de parede, timers, `useFrame`, transição ou animação CSS, `Easing.bounce` e `Easing.elastic` | FAIL |
| Corte que não casa com início de frase (tolerância de 0,25 s) | WARN |
| Cena acima de 2,6 palavras por segundo; cena com menos de 1 s | WARN |
| Todas as cenas com a mesma duração | WARN |
| Dois SFX a menos de 0,12 s; menos de 1 s de quadro final depois da última palavra | WARN |
| Curva criada fora de `lib/motion.ts`; tag HTML de mídia; emoji; muito mais `opacity` que transform | WARN |

WARN é heurística: leia, decida e diga na entrega o que ficou.

## Dailies (antes do render final, obrigatório)

1. Stills em lote: `node <skill>/scripts/stills.cjs Showcase` na pasta do projeto renderiza início, meio e fim de cada cena com um bundle e um browser só (21 frames em cerca de 7 s; a CLI leva 3 a 4 s por frame porque refaz os dois a cada chamada). Grava em `out/stills`.
2. `contact_sheet.py --stills out/stills -o out/sheet.png` monta a folha sem MP4.
3. Abra a imagem e responda PASS ou FIX por quadro. Se houver subagente disponível, entregue a folha e este checklist a um revisor que não escreveu o código.
4. Quando um feedback citar um momento, renderize aquele instante (`stills.cjs Showcase --times 12.4,12.6 --scale 1 --out out/sf`) e olhe antes de editar.
5. Draft em vídeo (`npx remotion render Showcase out/draft.mp4 --scale=0.5 $(python3 <skill>/scripts/gl.py Showcase)`) só quando o que está em dúvida é movimento ou ritmo: rode o `qa.py --timeline` nele.

Rodada em que só a voz mudou não pede folha nova: o usuário ouve `public/audio/mix.wav`.

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
| Emenda de loop (`--loop`) | diferença entre último e primeiro frame no nível de um passo normal |
| Avisos | cor sem marca BT.709, resolução do perfil, fps padrão, trecho parado acima de 1,5 s, frames pretos, leitura acima de 17 cps |
| Ritmo (`--timeline`) | por cena: energia de movimento, fração do tempo em respiro, maior respiro e posição do pico. Avisa cena sem respiro de 0,25 s, cena quase toda parada e peça sem contraste (cena mais agitada abaixo de 1,5x a mais calma) |

O medidor de ritmo é um medidor, não um juiz: os limiares foram ajustados em um único vídeo real e servem para apontar onde olhar na folha de contato.

## Entrega

- Renderize com `--color-space=bt709` (o `remotion.config.ts` do template já define): o MP4 sai h264 yuv420p faixa TV, marcado BT.709, com AAC 48 kHz e faststart.
- `deliver.py` confere isso e copia o vídeo sem reencode. Só reencoda (CRF 18) quando a origem chega em faixa cheia (`yuvj420p`) ou em outro pixel format. Comprimir a faixa de um arquivo que já está em faixa TV lava o contraste: preto vira cinza e o branco perde brilho.
- Perfis: `youtube` 1920x1080, `reels` e `tiktok` 1080x1920, `square` 1080x1080, `linkedin` 1920x1080.
- Entregue: `final.mp4`, `sheet.png` e o texto de créditos (campo `attribution` de cada item do `credits.json`, mais "made using Openverse" quando houver).

## Setup e problemas comuns

- Chrome: o Remotion baixa o Chrome Headless Shell na primeira renderização. Em rede restrita, aponte um Chromium local com `--browser-executable=<caminho>`.
- Fontes: `@remotion/google-fonts` baixa a fonte no render; sem rede, use fonte local com `@remotion/fonts` e `staticFile`.
- Render lento: use a flag que o `gl.py` devolve. Ele renderiza um trecho com o backend padrão, `vulkan` e `angle-egl`, e só troca o padrão por um que seja ao menos 20% mais rápido com SSIM de 0,99 ou mais; guarda em `out/gl.json` (`--force` mede de novo). Não fixe `--gl=vulkan` à mão: sem GPU ele roda em software sem avisar e pode dobrar o tempo. `--frames=0-60` testa trechos.
- Filtro SVG de tela cheia com seed por frame (o `<Grain>`) custa de 13% a 20% do render e, no backend padrão, impede o ganho de `--concurrency`: com ele ligado, 4, 6 e 8 abas levam o mesmo tempo. Motion blur também custa caro.
- 3D sem GPU: `--gl=swangle`.
