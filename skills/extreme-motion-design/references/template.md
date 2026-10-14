# Mapa do template (`assets/template/`)

```
package.json, tsconfig.json, remotion.config.ts   o config já fixa colorSpace bt709
gitignore                         vira .gitignore na cópia: ignora node_modules, out e .env
roteiro.json                      fonte do tempo: cenas, falas, marcas e SFX (scripts/score.py lê; references/score.md)
direction.json                    contrato de direção: conceito, lei visual, motivo, layout e entrada de cada cena
public/brand.json                 marca: cores, fontes e logo (scripts/brand.py escreve; theme.ts lê)
public/timeline.json              partitura escrita pelo score.py: fps, tamanho, duration, scenes, narration, music, sfx, loudness
public/cues.json                  marcas nomeadas, frases, palavras e batidas, em tempo absoluto
public/audio/                     narração, trilha, mix e credits.json
src/index.ts, src/Root.tsx        registra as composições a partir da partitura; a prop `format` troca o tamanho
src/theme.ts                      C (cores da marca), FONT, MONO, type (escala tipográfica)
src/lib/score.tsx                 <Scene id>, useScene(id) com at('marca'), WORDS, BEATS, cue()
src/lib/format.ts                 useFormat(): u (escala), text e action (áreas seguras), pick({youtube, reels, square})
src/lib/motion.ts                 tokens: ease, easeX, springs, dur; tween, keys, pop, stagger, stepped, loopPhase, loopNoise, wiggle, jitter;
                                  avançadas: anticipate, lag, cascade, squash, velocity, smear, timeRemap, pingPong, ticker
src/lib/shapes.ts                 circlePath, starPath, blobPath, roundedRectPath
src/lib/rig.ts                    twoBoneIK, fabrik, forwardKinematics, visemeFor
src/blocks/                       blocos prontos (gráficos, contador, moldura de aparelho, legenda, código, cursor...): references/blocks.md
src/components/Camera.tsx         Camera e Layer (zoom, pan, rotação, parallax por profundidade)
src/components/KineticWords.tsx   tipografia cinética sincronizada à narração; groupPhrases
src/components/Morph.tsx          morphPath (flubber)
src/components/Fx.tsx             BoilFilter (cel), Grain (grão e vinheta), Echo (trails), IrisReveal, MaskReveal, Shine, GooeyFilter
src/components/Tracking.tsx       Tracked, CornerPin, cornerPinMatrix
src/components/Probe.tsx          sonda de layout: mede o texto de cada still para o layout.py. Fica no fim da composição
src/scenes/Showcase.tsx           exemplo completo: 3 cenas ancoradas na narração, whip entre cortes, push-in, morph, rig em twos com boil, loop, microinteração
src/scenes/BlocksDemo.tsx         composição "Blocks": todos os blocos em sequência, para ver antes de usar
```

## Como começar um vídeo novo

1. Copie a pasta, renomeie `gitignore` para `.gitignore` e rode `npm install`. O arquivo vai sem o ponto porque alguns canais de instalação descartam arquivo oculto.
2. Troque `public/brand.json` pelo da marca (`scripts/brand.py`) e, se a fonte for outra, o import de `src/theme.ts`.
3. Escreva `direction.json` e `roteiro.json`, rode `score.py` e depois `lint.py`.
4. Crie as cenas em `src/scenes/` com `<Scene id>` e `useScene(id)`, blocos de `src/blocks/` e as primitivas. Use `Showcase.tsx` como referência de estrutura e apague o que não usar. Mantenha `<Probe />` no fim da composição.
5. Formato: `"format": "reels"` no roteiro. Para entregar mais de um, escreva tamanhos com `u` e posições com `pick()` de `useFormat()` e renderize com `render.cjs --formats`.
6. `npx remotion studio` abre o preview interativo quando houver tela; num agente sem tela, use `stills.cjs` e a folha de contato.
