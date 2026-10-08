# Técnicas: frame a frame, cel animation, stop motion, rigging e lip sync

## Frame a frame

- Sequência de desenhos: um SVG ou PNG por pose em `public/frames/`; troque por frame com `stepped(frame, 2)` (animação em twos) e `staticFile(\`frames/${String(i).padStart(3, '0')}.png\`)`.
- Sprite sheet: um PNG com N quadros; mostre com `overflow: hidden` e `translateX(-i * largura)`.
- Exposure sheet: mantenha uma tabela `xsheet.json` `[{frame, pose, visema}]` quando houver diálogo; ela é a fonte do frame a frame e do lip sync.
- Inbetweens: entre duas poses-chave em SVG com os mesmos pontos, interpole os atributos; com pontos diferentes, use `morphPath`.

## Cel animation (estética de animação tradicional)

- Anime em twos (`stepped(frame, 2)`) ou threes para personagens; deixe câmera e fundos contínuos.
- Line boil: `<BoilFilter id="boil" hold={2} scale={3.5} />` em `<defs>` e `filter="url(#boil)"` no grupo do traço.
- Cores chapadas com sombra em uma camada de tom mais escuro e borda de 4 a 8 px; sem gradiente.
- Smear frame: em movimentos muito rápidos, um frame esticado na direção do movimento substitui o motion blur.
- Holds de 6 a 12 frames em poses-chave para o olho ler a pose.

## Stop motion

- Tempo em degraus: `stepped(frame, 2)` ou `stepped(frame, 3)` em tudo, inclusive câmera.
- Imperfeição controlada: `jitter(seed, frame, 2, 1.5)` em posição e `jitter(seed, frame, 2, 0.6)` em rotação; nunca mais que 2 px.
- Textura física: fotos reais de papel ou massa como fundo, sombra de contato sob cada objeto, leve flicker de luz (opacidade da vinheta variando por degrau).
- Com fotos reais de objetos: fotografe cada pose, nomeie em ordem e trate como frame a frame em twos.

## Rigging 2D

- Hierarquia: cada osso é um `<g transform="translate(pivô) rotate(ângulo)">` dentro do pai; o pivô fica na articulação.
- FK: `forwardKinematics(root, comprimentos, ângulos)` para poses e ciclos (caminhada, aceno).
- IK de dois ossos: `twoBoneIK(ombro, alvo, l1, l2, bend)` para braço e perna; anime só o alvo.
- Cadeias (cauda, tentáculo, corda): `fabrik(poseDeRepouso, alvo)`; passe a pose de repouso a cada frame para manter o render determinístico.
- Movimento secundário: partes soltas seguem o pai com atraso de 2 a 4 frames (`spring` sobre o ângulo do pai com `frame - atraso`).
- Personagem pronto: Lottie (`@remotion/lottie`) ou Rive; com Rive, avance o estado por frame (tempo = frame / fps), nunca pelo relógio.

## Lip sync

- O Kokoro devolve fonemas com tempo: `narration.words.json` traz `ph` (fonemas de cada palavra). Para tempos por fonema, chame `create_timed` direto.
- `visemeFor(fonema)` mapeia para 9 bocas: rest, A, E, I, O, U, MBP, FV, L. Desenhe as 9 bocas e troque por frame, em twos.
- Feche a boca (MBP) 1 frame antes de consoantes labiais e segure vogais longas.

## Rigging 3D

- GLTF com SkinnedMesh no `@remotion/three`: carregue com `useGLTF` dentro de `delayRender`, crie um `AnimationMixer` e chame `mixer.setTime(frame / fps)` a cada frame. Nunca use `mixer.update(delta)`.
- IK 3D: `CCDIKSolver` do three/examples, recalculado a cada frame a partir da pose de repouso.
