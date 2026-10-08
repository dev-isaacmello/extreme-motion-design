---
name: extreme-motion-design
description: Cria vídeos de motion design de nível profissional por código (Remotion/React) com trilha licenciada, SFX sincronizados, narração opcional com voz suave em pt-BR ou inglês e QA automático antes da entrega. Use quando pedirem motion design, motion graphics, vídeo animado, explainer, vídeo de produto ou lançamento, reel ou TikTok animado, tipografia cinética, logo animado, animação de UI, loop, ou técnicas como keyframing, zoom in/out, morphing, rigging, frame a frame, cel animation, stop motion, rotoscopia, motion tracking, match moving, compositing e motion 3D. Also for animated video, kinetic typography, explainer with voiceover.
license: MIT
compatibility: Node 18+, Python 3.10+ (uv recomendado) e ffmpeg. Remotion é gratuito para indivíduos e empresas de até 3 pessoas; acima disso exige Company License. Rede opcional (trilha online, TTS por API, primeiro download do Kokoro pelo GitHub).
metadata:
  version: "1.0.0"
  author: "Isaac Mello"
---

# Motion Design

Produz vídeo de motion design por código, com áudio e verificação. O agente não enxerga o vídeo enquanto escreve código: por isso o fluxo obriga a olhar frames renderizados e a passar num QA numérico antes de entregar.

Caminhos abaixo são relativos à pasta desta skill (`<skill>`). Scripts Python declaram dependências inline (PEP 723): rode com `uv run <skill>/scripts/x.py`. Sem uv, use `pip install` das dependências do cabeçalho e `python3`.

## Fluxo obrigatório

1. **Brief em 5 linhas**: objetivo, público, formato (16:9, 9:16, 1:1), duração, tom e marca (cores, fonte). Se faltar formato ou duração, assuma 16:9, 30 fps, 15 a 30 s, e diga o que assumiu.
2. **Projeto**: copie `<skill>/assets/template/` para a pasta do vídeo e rode `npm install`. O template já traz tokens de movimento, câmera 2.5D, tipografia cinética, morph, rig, efeitos e tracking (mapa em `references/template.md`).
3. **Roteiro e narração primeiro** (se houver voz): escreva o roteiro, rode `tts.py` e use os tempos reais das palavras. O áudio é o relógio; o visual se ajusta a ele, nunca o contrário. Detalhes em `references/narration.md`.
4. **Partitura**: preencha `public/timeline.json` (duração, cenas, narração, trilha, eventos de SFX, loudness). Fronteiras de cena saem do início das frases da narração. Vídeo, mixagem e QA leem este mesmo arquivo.
5. **Trilha e SFX**: `music.py` (Incompetech, depois Openverse, depois geração local) e eventos de SFX na partitura. Todo arquivo baixado entra em `credits.json`. Detalhes em `references/audio.md`.
6. **Cenas**: construa com as primitivas do template. Leia só a referência da técnica que for usar (tabela abaixo) e a doutrina (`references/doctrine.md`) antes da primeira cena.
7. **Dailies (antes do render final)**: renderize stills ou um render rápido, gere a folha de contato e OLHE a imagem. Revise com o checklist de `references/qa.md`, corrija e repita até não haver FIX.
8. **Mixagem, render, entrega e gate**:
   ```bash
   uv run <skill>/scripts/mix.py public/timeline.json
   npx remotion render Showcase out/render.mp4 --codec=h264 --audio-codec=aac
   uv run <skill>/scripts/deliver.py out/render.mp4 -o out/final.mp4
   uv run <skill>/scripts/qa.py out/final.mp4 --profile youtube --words public/audio/narration.words.json
   uv run <skill>/scripts/contact_sheet.py out/final.mp4 --timeline public/timeline.json -o out/sheet.png
   ```
   Só entregue com `qa.py` sem FAIL. Entregue o MP4, a folha de contato e o texto de créditos.

## Regras inegociáveis

- Todo estado visual deriva de `useCurrentFrame()`. Proibido: transição/animação CSS, classes `animate-*`, `setTimeout`, `Date.now()`, `Math.random()` (use `random(seed)`), `useFrame()` do React Three Fiber. Senão o render pisca ou diverge do preview.
- Curvas e springs só dos tokens de `src/lib/motion.ts`: entrada `enter`/`sharp`, saída `exit`, mudança de posição ou forma `move`, zoom out e reveal `settle`, `linear` só para rotação contínua e loops. Nunca `bounce` ou `elastic`; overshoot só no elemento em foco.
- Uma ação principal por vez. Stagger total até 500 ms. Saída dura cerca de 75% da entrada. Primeira animação começa 0,1 a 0,3 s depois do corte. Pausa de 0,3 a 0,75 s antes do clímax.
- Texto fica na tela pelo menos 1,5 s + 0,3 s por palavra e no máximo 17 caracteres por segundo em pt-BR. No máximo 2 linhas de 32 a 42 caracteres.
- Safe area: ação dentro de 90% do quadro, texto dentro de 80%. Em 9:16 (1080x1920), texto entre y 360 e 1420.
- Motion blur só em 1 a 3 batidas rápidas por vídeo, nunca em texto que precisa ser lido.
- Nada com cara de gerado por IA: sem gradiente roxo de tela cheia, sem tudo entrando com fade, sem glow genérico, sem emoji, sem tudo centralizado. Uma cor de acento, contraste WCAG AA.
- Nenhum número, logo ou fato inventado na tela. Dado do usuário ou com fonte.
- Trilha só com licença `cc0`, `pdm` ou `by` (ou gerada). Nunca `nd`, `sa`, `nc`, sampling+ ou licença desconhecida.

## Roteador de técnicas

| Técnica | Referência | Primitiva ou script |
|---|---|---|
| Keyframing, motion smooth, easing, springs | `references/techniques-motion.md` | `keys()`, `tween()`, `pop()`, `springs` |
| Zoom in, zoom out, push-in, pan, whip pan, parallax, câmera na mão | `references/techniques-motion.md` | `<Camera>`, `<Layer depth>`, `wiggle()` |
| Motion graphics (formas, linhas, dados, logo) | `references/techniques-motion.md` | `shapes.ts`, `strokeDashoffset`, `@remotion/shapes` |
| Kinetic typography | `references/techniques-motion.md` | `<KineticWords>` com `narration.words.json` |
| Morphing | `references/techniques-motion.md` | `morphPath()` (flubber) |
| Seamless loop | `references/techniques-motion.md` | `loopPhase()`, `loopNoise()`, `qa.py --loop` |
| UX/UI motion e microinterações | `references/techniques-motion.md` | `springs.snappy`, cursor em arco, ripple |
| Frame a frame, cel animation, stop motion | `references/techniques-character.md` | `stepped()`, `<BoilFilter>`, `jitter()` |
| Rigging, IK, lip sync | `references/techniques-character.md` | `twoBoneIK()`, `fabrik()`, `forwardKinematics()`, `visemeFor()` |
| Motion 3D | `references/techniques-3d-compositing.md` | `@remotion/three` + `<ThreeCanvas>` |
| Compositing | `references/techniques-3d-compositing.md` | blend modes, máscaras, `<Grain>`, chroma key |
| Motion tracking | `references/techniques-3d-compositing.md` | `scripts/track.py` + `<Tracked>` |
| Match moving | `references/techniques-3d-compositing.md` | `track.py --quad` + `<CornerPin>`, `scripts/matchmove.py` |
| Rotoscopia | `references/techniques-3d-compositing.md` | `scripts/roto.py` (PNG com alfa ou contornos SVG) |

Áudio (`references/audio.md`), narração (`references/narration.md`), QA e entrega (`references/qa.md`), doutrina de movimento (`references/doctrine.md`), mapa do template (`references/template.md`).

## Comandos de áudio e voz

```bash
uv run <skill>/scripts/tts.py roteiro.txt -o public/audio/narration --voice pf_dora --speed 0.92   # F; pm_alex ou pm_santa (M)
uv run <skill>/scripts/tts.py --normalize-only "Plano de R$ 49,90 às 14h30 com IA"                 # confira a pronúncia
uv run <skill>/scripts/music.py incompetech --feel calm --bpm 70-110 --min-sec 60 -o public/audio/music.mp3
uv run <skill>/scripts/music.py generate --sec 30 --bpm 84 --mood calm -o public/audio/music.wav   # offline
uv run <skill>/scripts/beats.py public/audio/music.mp3 --fps 30                                  # cortes na batida
uv run <skill>/scripts/sfx.py --all public/audio/sfx                                             # whoosh, pop, click...
```

Voz premium opcional: `--provider elevenlabs` (tempos reais por caractere), `azure` ou `openai` (tempos estimados). Pergunte ao usuário antes de usar API paga.

## Quando parar e perguntar

- Logo, marca, número ou depoimento que o usuário não forneceu.
- Uso de API paga (voz, música) ou trilha com licença diferente de cc0, pdm ou by.
- Empresa do usuário com mais de 3 pessoas usando Remotion: avise da Company License.
