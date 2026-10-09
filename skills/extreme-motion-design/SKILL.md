---
name: extreme-motion-design
description: Cria vídeos de motion design de nível de estúdio por código (Remotion/React), com trilha licenciada, SFX sincronizados, voz opcional (ElevenLabs ou modelo TTS local escolhido pelo hardware) e gates automáticos de lint e QA antes da entrega. Use quando pedirem motion design, motion graphics, vídeo animado, explainer, vídeo de produto ou lançamento, reel ou TikTok animado, tipografia cinética, logo animado, animação de UI, loop, narração ou voiceover para vídeo, ou técnicas como keyframing, zoom in e zoom out, motion smooth, morphing, rigging, frame a frame, cel animation, stop motion, rotoscopia, motion tracking, match moving, compositing, motion 3D, speed ramp, match cut, overshoot, parallax e transições. Also for animated video, kinetic typography, product launch video, explainer with voiceover, text to speech narration.
license: MIT
compatibility: Node 18+, Python 3.10+ (uv recomendado) e ffmpeg. Remotion é gratuito para indivíduos e empresas de até 3 pessoas; acima disso exige Company License. Rede opcional (trilha online, voz por API, download de modelos de voz). Voz local funciona em CPU; modelos maiores pedem GPU.
metadata:
  version: "1.2.1"
  author: "Isaac Mello"
---

# Motion Design

Produz vídeo de motion design por código, com áudio e verificação. O agente não enxerga o vídeo enquanto escreve código: por isso o fluxo mede antes de renderizar (`lint.py`), obriga a olhar frames renderizados e só entrega depois de um gate numérico (`qa.py`).

Caminhos são relativos à pasta desta skill (`<skill>`). Scripts com dependências declaram tudo inline (PEP 723): rode com `uv run <skill>/scripts/x.py`. `voice.py`, `lint.py` e `gl.py` usam só a biblioteca padrão e rodam com `python3`; `stills.cjs` roda com `node` na pasta do projeto.

## Fluxo obrigatório

1. **Brief em 5 linhas**: objetivo, público, formato (16:9, 9:16, 1:1), duração, tom e marca (cores, fonte). Se faltar formato ou duração, assuma 16:9, 30 fps, 15 a 30 s, e diga o que assumiu.
2. **Pergunta de voz (sempre)**: rode `python3 <skill>/scripts/voice.py` e faça ao usuário a pergunta que ele imprime, com as três opções: **sem voz**, **voz com ElevenLabs** (o script traz o passo a passo da chave) ou **voz local** (o script recomenda o modelo que cabe no hardware medido). Use a ferramenta de pergunta do agente quando existir, senão pergunte em texto, e espere a resposta. Não escolha pelo usuário. Só dispense quando o pedido já respondeu com todas as letras. Detalhes de cada caminho em `references/narration.md`.
3. **Projeto**: copie `<skill>/assets/template/` para a pasta do vídeo, renomeie `gitignore` para `.gitignore` (é ele que mantém o `.env` fora do git) e rode `npm install`. Mapa das primitivas em `references/template.md`.
4. **Roteiro e voz primeiro** (se houver voz): escreva o roteiro, gere o áudio pelo caminho escolhido e use os tempos reais das palavras. O áudio é o relógio; o visual se ajusta a ele, nunca o contrário.
5. **Partitura**: preencha `public/timeline.json` (duração, cenas, narração, trilha, eventos de SFX, loudness). Fronteiras de cena saem do início das frases. Vídeo, mixagem, lint e QA leem este mesmo arquivo.
6. **Trilha e SFX**: `music.py` (Incompetech, depois Openverse, depois geração local) e eventos de SFX na partitura. Todo arquivo baixado entra em `credits.json`. Detalhes em `references/audio.md`.
   **Aprovação do áudio (com voz)**: rode `mix.py` e entregue `public/audio/mix.wav` para o usuário ouvir antes do render final. Pedido que muda só a voz refaz voz, partitura e mix e volta para o usuário ouvir, sem render e sem folha de contato, até a voz ser aprovada.
7. **Direção antes de animar**: leia `references/direction.md` e a doutrina (`references/doctrine.md`). Faça 3 a 5 styleframes com `stills.cjs --times` e olhe cada um antes de animar.
8. **Cenas**: construa com as primitivas do template. Leia só a referência da técnica que for usar (roteador abaixo).
9. **Lint (antes de todo render)**: `python3 <skill>/scripts/lint.py` na pasta do projeto. Corrija todo FAIL; avalie cada WARN.
10. **Dailies**: `node <skill>/scripts/stills.cjs <Composição>` gera os frames de início, meio e fim de cada cena em um processo só, e `contact_sheet.py --stills out/stills` monta a folha sem precisar de MP4. OLHE a imagem, revise com o checklist de `references/qa.md`, corrija e repita até não haver FIX. Para ver vários frames nunca chame `remotion still` em laço: cada chamada refaz o bundle e abre outro browser.
11. **Mixagem, render, entrega e gate**:
    ```bash
    uv run <skill>/scripts/mix.py public/timeline.json
    npx remotion render Showcase out/render.mp4 --codec=h264 --audio-codec=aac --color-space=bt709 $(python3 <skill>/scripts/gl.py Showcase)
    uv run <skill>/scripts/deliver.py out/render.mp4 -o out/final.mp4
    uv run <skill>/scripts/qa.py out/final.mp4 --profile youtube --timeline public/timeline.json --words public/audio/narration.words.json --stills out/stills
    uv run <skill>/scripts/contact_sheet.py out/final.mp4 --timeline public/timeline.json -o out/sheet.png
    ```
    `gl.py` mede uma vez por projeto qual backend gráfico renderiza mais rápido com a mesma imagem e devolve a flag (ou nada). `deliver.py` copia o vídeo sem reencode quando o render já está certo. `--stills` faz o `qa.py` reprovar MP4 com contraste diferente dos stills. Só entregue com `qa.py` sem FAIL. Entregue o MP4, a folha de contato e o texto de créditos, e diga o que ficou em WARN.

## Regras inegociáveis

- Todo estado visual deriva de `useCurrentFrame()`. Proibido: transição ou animação CSS, classes `animate-*`, `setTimeout`, `Date.now()`, `Math.random()` (use `random(seed)`), `useFrame()` do React Three Fiber. Senão o render pisca ou diverge do preview. `lint.py` reprova.
- Curvas e springs só dos tokens de `src/lib/motion.ts`: entrada `enter` ou `sharp`, saída `exit`, mudança de posição ou forma `move`, zoom out e reveal `settle`, herói da cena `easeX.emphasized`, `linear` só para rotação contínua e loops. Nunca `bounce` ou `elastic`. Overshoot é um só (`easeX.overshoot` ou `springs.snappy`) e só no elemento em foco.
- Uma ação primária por vez; secundárias de até 30% da amplitude e ambiente de até 5%. Stagger total até 500 ms. Saída dura cerca de 75% da entrada. Primeira animação começa 0,1 a 0,3 s depois do corte. Depois de cada chegada, hold de 0,4 a 0,8 s; pausa de 0,3 a 0,75 s antes do clímax.
- Texto fica na tela pelo menos 1,5 s + 0,3 s por palavra e no máximo 17 caracteres por segundo em pt-BR. No máximo 2 linhas de 32 a 42 caracteres.
- Safe area: ação dentro de 90% do quadro, texto dentro de 80%. Em 9:16 (1080x1920), texto entre y 360 e 1420.
- Motion blur só em 1 a 3 batidas rápidas por vídeo, nunca em texto que precisa ser lido.
- Nada com cara de gerado por IA: sem gradiente roxo de tela cheia, sem tudo entrando com fade, sem glow genérico, sem emoji, sem tudo centralizado. Uma cor de acento, contraste WCAG AA.
- Nenhum número, logo ou fato inventado na tela. Dado do usuário ou com fonte.
- Trilha só com licença `cc0`, `pdm` ou `by` (ou gerada). Nunca `nd`, `sa`, `nc`, sampling+ ou licença desconhecida.
- Chave de API nunca entra no chat, em comando, em log ou em arquivo versionado. O usuário grava no `.env` do projeto.

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
| Antecipação, overshoot, follow-through, squash e stretch, smear | `references/techniques-advanced.md` | `anticipate()`, `easeX`, `lag()`, `squash()`, `smear()` |
| Cascata, speed ramp, time remap, curva de velocidade | `references/techniques-advanced.md` | `cascade()`, `timeRemap()`, `velocity()` |
| Match cut, morph cut, corte invisível, J-cut e L-cut, íris, transição por forma e líquida | `references/techniques-advanced.md` | `<IrisReveal>`, `<GooeyFilter>`, `@remotion/transitions` |
| Mattes, trim paths, repeater, baseline reveal, contador, eco, shine, look de lente | `references/techniques-advanced.md` | `<MaskReveal>`, `ticker()`, `<Echo>`, `<Shine>`, `<Grain>` |
| Frame a frame, cel animation, stop motion | `references/techniques-character.md` | `stepped()`, `<BoilFilter>`, `jitter()` |
| Rigging, IK, lip sync | `references/techniques-character.md` | `twoBoneIK()`, `fabrik()`, `forwardKinematics()`, `visemeFor()` |
| Motion 3D | `references/techniques-3d-compositing.md` | `@remotion/three` + `<ThreeCanvas>` |
| Compositing | `references/techniques-3d-compositing.md` | blend modes, máscaras, `<Grain>`, chroma key |
| Motion tracking | `references/techniques-3d-compositing.md` | `scripts/track.py` + `<Tracked>` |
| Match moving | `references/techniques-3d-compositing.md` | `track.py --quad` + `<CornerPin>`, `scripts/matchmove.py` |
| Rotoscopia | `references/techniques-3d-compositing.md` | `scripts/roto.py` (PNG com alfa ou contornos SVG) |

Direção e estrutura de batidas (`references/direction.md`), voz (`references/narration.md`), áudio (`references/audio.md`), QA e entrega (`references/qa.md`), doutrina de movimento (`references/doctrine.md`), mapa do template (`references/template.md`).

## Comandos de voz e áudio

```bash
python3 <skill>/scripts/voice.py                                   # mede o hardware e monta a pergunta de voz
python3 <skill>/scripts/voice.py --check-key                       # valida a chave da ElevenLabs sem gastar
python3 <skill>/scripts/voice.py --audition "Primeira frase." -o out/vozes   # mesma frase em cada voz local
uv run <skill>/scripts/tts.py roteiro.txt -o public/audio/narration --voice pf_dora --speed 0.92     # Kokoro local
uv run <skill>/scripts/tts.py roteiro.txt -o public/audio/narration --provider elevenlabs --voice <voice_id>
uv run <skill>/scripts/align.py public/audio/narration.wav roteiro.txt    # tempos por palavra para qualquer WAV
uv run <skill>/scripts/tts.py --normalize-only "Plano de R$ 49,90 às 14h30 com IA"                  # confira a pronúncia
uv run <skill>/scripts/music.py incompetech --feel calm --bpm 70-110 --min-sec 60 -o public/audio/music.mp3
uv run <skill>/scripts/music.py generate --sec 30 --bpm 84 --mood calm -o public/audio/music.wav    # offline
uv run <skill>/scripts/beats.py public/audio/music.mp3 --fps 30                                   # cortes na batida
uv run <skill>/scripts/sfx.py --all public/audio/sfx                                              # whoosh, pop, click...
```

## Quando parar e perguntar

- A pergunta de voz do passo 2.
- Logo, marca, número ou depoimento que o usuário não forneceu.
- Antes de gastar em API paga (voz, música): diga o tamanho do roteiro em caracteres e espere o sim.
- Trilha com licença diferente de cc0, pdm ou by.
- Empresa do usuário com mais de 3 pessoas usando Remotion: avise da Company License.
