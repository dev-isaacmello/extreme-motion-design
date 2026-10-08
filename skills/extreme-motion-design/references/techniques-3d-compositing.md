# Técnicas: motion 3D, compositing, motion tracking, match moving e rotoscopia

## Motion 3D (`@remotion/three`)

```tsx
<ThreeCanvas width={width} height={height} camera={{fov: 40, position: [0, 0, 6]}}>
  <ambientLight intensity={0.6} /><directionalLight position={[3, 4, 5]} />
  <mesh rotation={[0, frame * 0.02, 0]}><torusKnotGeometry args={[1, 0.3, 160, 24]} /><meshStandardMaterial color="#FFB547" /></mesh>
</ThreeCanvas>
```
- Tudo pelo frame; `useFrame()` é proibido. Câmera animada com `tween`/`keys` sobre posição e `lookAt`.
- Look cel em 3D: `meshToonMaterial` com `gradientMap` de 3 tons e contorno por casco invertido (mesh escalado 1,03 com `side: BackSide` preto).
- Render sem GPU: se o WebGL falhar, use `--gl=swangle` (ou `angle` em máquina com GPU). 3D em CPU é lento: teste com `--frames=0-30` antes.
- Ativos: GLTF/GLB em `public/`, carregados com `delayRender`/`continueRender`.

## Compositing

- Camadas: fundo, plano médio, sujeito, texto, efeitos. Cada camada um `AbsoluteFill`.
- Blend modes: `mixBlendMode: 'screen'` para luz e brilho, `multiply` para sombra e textura de papel, `overlay` para grão.
- Máscaras: `clipPath`, `mask-image` com gradiente, ou SVG `<mask>`; texto atrás do sujeito usa a máscara de `roto.py`.
- Chroma key: pré-processe com ffmpeg (`chromakey=0x00FF00:0.12:0.08,despill=green`) para WebM com alfa (`-c:v libvpx-vp9 -pix_fmt yuva420p`) e use `<OffthreadVideo transparent>`.
- Integração: grão (`<Grain>`) por cima de tudo, vinheta leve, light wrap (blur da luz de fundo vazando 4 a 8 px na borda do sujeito com `screen`), sombra de contato.
- Vídeo como camada: `<OffthreadVideo src={staticFile('footage.mp4')} />`. Saída com alfa: `--codec=prores --prores-profile=4444` ou WebM VP9.

## Motion tracking

```bash
uv run <skill>/scripts/track.py footage.mp4 --point 812,430 -o public/track/logo.json --smooth 5
```
```tsx
import track from '../public/track/logo.json';
<Tracked track={track} offset={{x: 0, y: -80}}><Label /></Tracked>
```
- KLT (Lucas-Kanade) sobre cantos detectados em volta do ponto; refaz os pontos quando somem. Bom para logo, rosto, objeto com textura.
- Escolha um ponto com textura e contraste; superfícies lisas não rastreiam.
- Suavize (`--smooth`) para overlays; não suavize quando o elemento precisa colar no pixel.

## Match moving

- Plano (tela de celular, placa, parede): `track.py --quad x0,y0,x1,y1,x2,y2,x3,y3` (TL, TR, BR, BL) e `<CornerPin track width height>` para colar a UI no plano com perspectiva correta.
- Câmera 3D a partir do plano: `matchmove.py public/track/screen.json --plane 0.07x0.15 --fov 60 --size 1920x1080` gera posição e quaternion por frame para a câmera do Three.js; objetos 3D ficam presos ao plano (z = 0).
- Cena sem plano dominante: resolva a câmera no Blender (Movie Clip Editor, libmv) ou COLMAP e exporte para JSON; é a mesma estrutura de câmera por frame.
- Valide com `matchmove.py --selftest` e com a folha de contato: os cantos devem cair nos cantos reais em início, meio e fim.

## Rotoscopia

```bash
uv run <skill>/scripts/roto.py footage.mp4 --backend rembg -o public/roto --svg
```
- `rembg`: pessoa ou objeto em destaque, baixa o modelo do GitHub, cerca de 1 a 3 fps em CPU.
- `mog2`: câmera fixa, separa o que se move do fundo. `chroma`: fundo de cor sólida.
- Saídas: PNG com alfa por frame (`<Img src={staticFile(\`roto/frame_${i}.png\`)} />`) e `contours.json` com paths SVG por frame para roto estilizado (traço desenhado, preenchimento chapado, em twos).
- Qualidade de cinema (cabelo, movimento rápido): SAM 2 ou MatAnyone em GPU; o formato de saída é o mesmo.
