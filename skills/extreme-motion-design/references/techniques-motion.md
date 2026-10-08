# Técnicas: keyframing, câmera, motion graphics, tipografia, morph, loops e UI

## Keyframing e motion smooth

```tsx
const frame = useCurrentFrame();
const x = keys(frame, [0, 15, 45, 60], [-400, 0, 0, 400], [ease.enter, ease.linear, ease.exit]); // entra, segura, sai
const s = pop(frame, fps, 10, springs.snappy); // 0 -> 1 com spring a partir do frame 10
```
- Smooth vem de três coisas: easing correto por segmento, hold entre movimentos e motion blur pontual. Nunca encadeie keyframes sem hold.
- Caminho curvo: anime um progresso 0..1 e leia o ponto com `getPointAtLength` de `@remotion/paths` (ou `evolvePath` para desenhar o traço).
- Frames sempre a partir de segundos com o fps da composição: `sec(1.2, fps)`.

## Câmera: zoom in, zoom out, push-in, pan, whip, parallax

```tsx
<Camera zoom={tween(frame, 0, 120, 1, 1.12, ease.move)} x={wiggle('cx', frame, 0.03, 6)}>
  <Layer depth={3}>{/* fundo: move 1/3 */}</Layer>
  <Layer depth={1}>{/* plano focal */}</Layer>
  <Layer depth={0.7}>{/* primeiro plano: move mais */}</Layer>
</Camera>
```
- Push-in: zoom 1 para 1,08 a 1,15 ao longo da cena com `ease.move`. Zoom out de revelação: 1,15 para 1 com `ease.settle`.
- Zoom em ponto: combine `zoom` com `x`/`y` apontando o alvo (coordenadas do mundo em px a partir do centro).
- Whip pan: deslocamento rápido de ~12% do quadro em 6 a 8 frames com blur; use o componente `Whip` do Showcase como modelo.
- Dolly zoom (vertigo): aumente o zoom da camada de fundo enquanto reduz o do plano focal.
- Motion blur: `@remotion/motion-blur` (`<CameraMotionBlur shutterAngle={180} samples={8}>`) em cortes e batidas rápidas; custa N vezes o render.

## Motion graphics

- Linhas que se desenham: `pathLength={1}`, `strokeDasharray={1}`, `strokeDashoffset={tween(...)}`.
- Formas: `circlePath`, `starPath`, `blobPath`, `roundedRectPath` em `shapes.ts`, ou `@remotion/shapes`.
- Números e gráficos: contador com `Math.round(tween(...))` e `toLocaleString('pt-BR')`; barras com `scaleY` e origem embaixo. Nunca invente dado.
- Logo reveal: máscara (`clipPath` ou `overflow: hidden`) com o logo subindo, depois traço desenhando o contorno; segure 1 s.

## Kinetic typography

- `<KineticWords words={narration.words} offsetSec={timeline.narration.start} />`: cada palavra sobe por máscara 3 frames antes de ser falada e a palavra falada recebe o acento.
- Padrões: palavra por palavra (ênfase), frase com stagger (legenda viva), escala de ênfase numa palavra-chave, texto em caminho (`<textPath>`), letras com stagger de 1 a 2 frames só em títulos curtos.
- Meça texto com `@remotion/layout-utils` (`measureText`, `fitText`) antes de escolher tamanho; nunca deixe a linha estourar a safe area.

## Morphing

```tsx
const shapes = [circlePath(960, 540, 200), starPath(960, 540, 240), blobPath(960, 540, 220, 'b')];
const p = keys(frame, [0, 12, 30, 48, 66], [0, 0, 1, 1, 2], [ease.move, ease.move, ease.move, ease.move]);
<path d={morphPath(shapes, p)} />
```
- flubber resolve formas com número de pontos diferente. Segure cada forma e transicione com `ease.move` em 15 a 20 frames.
- Ícone para ícone: use paths de um único contorno; para formas com furos, morph de cada subpath separado.
- Alternativa líquida: filtro gooey (blur + `feColorMatrix` de alfa) com círculos se fundindo.

## Seamless loop

- O período divide a duração: cena de 90 frames com período 45 ou 90. O frame `period` deve ser igual ao frame 0.
- Use `loopPhase(frame, period)` para ângulos (`phase * 2π`) e `loopNoise(seed, frame, period)` para ruído que fecha.
- Rotação de figura com simetria de N lados: gire `360 / N` graus por período.
- Verifique: `qa.py out/loop.mp4 --loop`. Exporte GIF com `npx remotion render ... --codec=gif` ou WebM para web.

## UX/UI motion e microinterações

- Durações de UI: 100 a 300 ms (3 a 9 frames a 30 fps); quanto maior o elemento ou a distância, maior a duração.
- Feedback de clique: escala 1 para 0,96 e de volta em 4 a 6 frames, ripple de 12 a 16 frames, toggle com `springs.snappy`.
- Cursor de demo: chega em arco com `ease.move`, para 2 a 4 frames antes de clicar, clique com SFX `click`.
- Demo de produto: grave a tela ou recrie a UI em React; dê push-in no ponto de interesse (zoom 1,4 a 1,8) e volte com `ease.settle`.
- Para animação dentro do produto (não vídeo), respeite `prefers-reduced-motion`; essa skill gera vídeo, então descreva a especificação em ms e curvas para o time.
