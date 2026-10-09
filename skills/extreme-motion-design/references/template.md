# Mapa do template (`assets/template/`)

```
package.json, tsconfig.json, remotion.config.ts
public/timeline.json              partitura: fps, tamanho, duration, scenes, narration, music, sfx, loudness, audio
public/audio/narration.words.json saída do tts.py (substitua pela sua)
src/index.ts, src/Root.tsx        registra a composição a partir da partitura
src/lib/motion.ts                 tokens: ease, easeX, springs, dur; tween, keys, pop, stagger, stepped, loopPhase, loopNoise, wiggle, jitter;
                                  avançadas: anticipate, lag, cascade, squash, velocity, smear, timeRemap, pingPong, ticker
src/lib/shapes.ts                 circlePath, starPath, blobPath, roundedRectPath
src/lib/rig.ts                    twoBoneIK, fabrik, forwardKinematics, visemeFor
src/components/Camera.tsx         Camera e Layer (zoom, pan, rotação, parallax por profundidade)
src/components/KineticWords.tsx   tipografia cinética sincronizada à narração; groupPhrases
src/components/Morph.tsx          morphPath (flubber)
src/components/Fx.tsx             BoilFilter (cel), Grain (grão e vinheta), Echo (trails), IrisReveal, MaskReveal, Shine, GooeyFilter
src/components/Tracking.tsx       Tracked, CornerPin, cornerPinMatrix
src/scenes/Showcase.tsx           exemplo completo: 3 cenas ancoradas na narração, whip entre cortes, push-in, morph, rig em twos com boil, loop, microinteração
```

## Como começar um vídeo novo

1. Copie a pasta, rode `npm install`.
2. Gere a narração em `public/audio/` (se houver voz), depois ajuste `public/timeline.json` (cenas a partir das frases) e rode `lint.py`.
3. Crie as cenas em `src/scenes/` reaproveitando as primitivas; use `Showcase.tsx` como referência de estrutura e apague o que não usar.
4. Para 9:16, mude `width` e `height` na partitura e revise a safe area.
5. `npx remotion studio` abre o preview interativo quando houver tela; num agente sem tela, use stills e a folha de contato.
