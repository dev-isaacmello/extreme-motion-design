# QA, dailies e entrega

## Dailies (antes do render final, obrigatório)

1. Render rápido: `npx remotion render Showcase out/draft.mp4 --scale=0.5` (ou stills: `npx remotion still Showcase out/f45.png --frame=45`).
2. `contact_sheet.py out/draft.mp4 --timeline public/timeline.json -o out/sheet.png` pega início, meio e fim de cada cena.
3. Abra a imagem e responda PASS ou FIX por quadro. Se houver subagente disponível, entregue a folha e este checklist a um revisor que não escreveu o código.
4. Quando um feedback citar um momento, extraia aquele frame (`ffmpeg -ss <t> -i out/draft.mp4 -frames:v 1 f.png`) e olhe antes de editar.

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
| Áudio | AAC presente e duração igual à do vídeo (até 0,15 s) |
| Loudness | alvo do perfil até 1 LU; true peak até o máximo do perfil |
| Flashes | no máximo 3 por segundo (aproximação da WCAG 2.3.1) |
| Emenda de loop (`--loop`) | diferença entre último e primeiro frame no nível de um passo normal |
| Avisos | resolução do perfil, fps padrão, trecho parado acima de 1,5 s, frames pretos, leitura acima de 17 cps |

## Entrega

- `deliver.py` reencoda para yuv420p faixa TV, BT.709, faststart e AAC 48 kHz (CRF 18).
- Perfis: `youtube` 1920x1080, `reels` e `tiktok` 1080x1920, `square` 1080x1080, `linkedin` 1920x1080.
- Entregue: `final.mp4`, `sheet.png` e o texto de créditos (campo `attribution` de cada item do `credits.json`, mais "made using Openverse" quando houver).

## Setup e problemas comuns

- Chrome: o Remotion baixa o Chrome Headless Shell na primeira renderização. Em rede restrita, aponte um Chromium local com `--browser-executable=<caminho>`.
- Fontes: `@remotion/google-fonts` baixa a fonte no render; sem rede, use fonte local com `@remotion/fonts` e `staticFile`.
- Render lento: `--concurrency` igual ao número de núcleos; `--frames=0-60` para testar trechos; motion blur e filtros SVG de tela cheia custam caro.
- 3D sem GPU: `--gl=swangle`.
