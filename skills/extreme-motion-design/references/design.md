# Design: o que separa um quadro de estúdio do quadro padrão do modelo

`doctrine.md` cuida de movimento. Esta referência cuida do quadro parado: composição, tipografia, cor, textura, imagem real, estrutura de filme e som. Leia antes de propor direções (passo 5 do fluxo) e escolha entre as seis direções do fim, ou derive uma do assunto com a mesma ficha.

Como ler: cada regra traz a origem. `[fonte: URL]` foi lido na fonte; `[consenso de prática]` é prática corrente sem norma; `[inferência minha]` é síntese de quem escreveu. Quase todo limiar numérico de design é prática ou inferência, não norma: os de `design.py` saem como aviso. Os números de filmes de lançamento vêm de teardowns sem método publicado e de um estudo de fornecedor (Advids): use como hipótese. Ninguém assistiu aos filmes citados para escrever isto; o que há sobre estúdios vem de texto.

Onde esta referência e a doutrina discordam, vale esta: título não precisa ter peso 600 a 800 (T10) e a peça pode ter mais de um acento, desde que cada cor tenha papel e área medida (K2, K3).

## Sumário

1. Composição (C1 a C12)
2. Tipografia (T1 a T14)
3. Cor e textura (K1 a K10)
4. Linguagem de estúdio (tabela, E1 a E4)
5. Filme de lançamento de 60 a 90 s (L1 a L12)
6. Motion sobre imagem real (F1 a F9)
7. Som (S1 a S9)
8. Tendências e clichês de 2025 e 2026
9. Sinais de gerado em design, com antídoto
- As 15 regras que mais mudam o resultado
- Seis direções de arte

## O achado que motivou esta referência

O quadro que o modelo puro entrega (condensada gigante à esquerda, duas cores chapadas, contador mono no canto) é exatamente dois dos cinco "segundos padrões" que a skill frontend-design da Anthropic lista: **"dark signal"** (quase preto com um acento ácido ou vermelhão) e **"template chrome"** (rótulo em caixa alta com tracking, mono em rótulo pequeno, marcadores 01/02/03, strings "A · B · C", seta em todo link), mais o padrão "número grande, rótulo pequeno, stats de apoio". Quando se proíbe roxo e Inter, o agente cai nisso ou em "creme + serifada + terracota". Proibir não resolve: a direção tem de ser derivada do assunto e verificada por medida. [fonte: https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md e https://capitalandcompute.net/blog/fix-ai-slop-design/]

## Métricas de frame (o que `scripts/design.py` mede)

Usadas nas regras abaixo. As definições são nossas. `design.py` mede hoje as marcadas com (medida); as outras ficam como critério de revisão da folha.

- `ratio_top2` (medida): maior font-size renderizado / segundo maior.
- `n_sizes` (medida): font-sizes distintos no frame (tolerância 4%).
- `empty_frac` (medida): fração de pixels a menos de ΔE_OK 0,02 da cor de fundo dominante.
- `n_colors_2pct` (medida): clusters em OKLCH (L, C, h quantizados) com 2% ou mais da área.
- `chroma_frac` (medida): fração de pixels com C acima de 0,10.
- `mass_offset` (medida): distância do centroide da massa visual (peso = |L do pixel menos L do fundo|) ao centro do quadro, dividida pela meia diagonal.
- `n_left_edges`: bordas esquerdas distintas dos blocos (tolerância 4 px) = colunas reais em uso.
- `bleed_count`: elementos que cruzam a borda do quadro.
- `depth_levels`: combinações distintas de blur e escala por camada.
- `grain_sigma`: desvio padrão de alta frequência numa área chapada.
- `mono_frac`, `caps_frac` (medida): fração dos blocos de texto em fonte mono e em caixa alta.

---

## 1. Composição para quadro em movimento

**C1. Grade declarada em unidades, não em "à esquerda".** 16:9: 12 colunas, margem de 5% da largura (96 px em 1920), calha de 1,25% (24 px). 9:16: 6 colunas, margem de 6,7% (72 px em 1080). Linhas: módulo de 1/8 da altura útil. Por quê: sem grade o agente alinha tudo na margem esquerda e para. Aplicar: `const col = (n) => M + n * (colW + G)`; cada bloco declara coluna inicial e span. Medir: `n_left_edges` entre 2 e 4 por frame; 1 em toda cena = espinha única. [consenso de prática; números inferência minha]

**C2. Razão áurea não é ferramenta de trabalho.** Use divisões simples: 1/3 e 2/3, 5/7, 3/5. A matéria da Fast Company diz que muitos designers não usam e que não há ciência por trás; a ideia estética vem de Pacioli, não de Euclides. Aplicar: se quiser a proporção, ela entra como razão de escala tipográfica (1,618), não como espiral sobre o quadro. [fonte: https://www.fastcompany.com/3044877/the-golden-ratio-designs-biggest-myth, lido via resumo de busca; https://talesoftimesforgotten.com/2019/11/08/were-the-greeks-really-obsessed-with-the-golden-ratio/]

**C3. Terços servem para o ponto de atenção, não para o bloco de texto.** O herói fica num dos quatro cruzamentos ou sangra por uma borda; nunca no centro geométrico por padrão e nunca sempre no mesmo cruzamento. Medir: `mass_offset` entre 0,12 e 0,45 na maioria das cenas; abaixo de 0,05 só em cena declarada simétrica (logo, fecho). Reprovar a peça se o desvio padrão de `mass_offset` entre cenas for menor que 0,05 (mesma composição). [consenso de prática; limiares inferência minha]

**C4. Simetria dinâmica como eixo de movimento.** Use a diagonal do quadro e a perpendicular que sai do canto oposto (armadura de Hambidge) para inclinar elementos e trajetórias: em 16:9 a diagonal faz 29,4 graus, em 9:16 faz 60,6 graus. Elementos inclinados usam esse ângulo ou o complemento, não 15 ou 45 por hábito. Medir: ângulos de `rotate` fora de {0, 90, ângulo da diagonal, complemento} viram aviso. [consenso de prática para a armadura; aplicação a motion é inferência minha]

**C5. Espaço negativo é número.** Quadro de marca ou de produto: `empty_frac` de 55 a 80%. Quadro de dado ou UI: 30 a 50%. Abaixo de 25% só em colagem declarada. Por quê: a pesquisa de Pracejus, Olsen e O'Guinn liga espaço em branco a prestígio e qualidade percebida (sem percentual publicado nos resumos que li); o texto sobre os filmes da Apple atribui o "caro" a uma ideia por plano e vazio. Medir: `empty_frac`. [fonte do porquê: https://ideas.repec.org/a/oup/jconrs/v33y2006i1p82-90.html e https://youmind.com/landing/x-viral-articles/apple-product-video-design-secrets (opinião de dono de estúdio); faixas inferência minha]

**C6. Vazio é assimétrico.** O espaço vazio fica concentrado de um lado (uma margem com 2x ou mais a oposta), não distribuído igual em volta. Medir: razão entre a maior e a menor margem livre ao redor da caixa do conteúdo, 2 ou mais. [consenso de prática]

**C7. Contraste de escala entre níveis: salte, não suba degrau.** Hero / secundário de 3:1 ou mais em quadro tipográfico (escalas modulares de 1,25 a 1,5 são de página de leitura; em quadro de vídeo, pule dois ou três degraus). Três tamanhos por frame, no máximo quatro. Medir: `ratio_top2` 3 ou mais; `n_sizes` 4 ou menos. `ratio_top2` entre 1,2 e 2 é a zona morta (nem igual, nem contraste). [consenso de prática: escala modular; limiar 3:1 inferência minha]

**C8. Tensão: uma coisa sangra.** Pelo menos um elemento por cena cruza a borda ou é cortado pela máscara do quadro (tipo, foto, forma). Quadro em que tudo cabe com folga lê como slide. Medir: `bleed_count` 1 ou mais em pelo menos metade das cenas. [consenso de prática]

**C9. Direção de leitura declarada.** Cada cena define entrada e saída do olho (canto superior esquerdo para inferior direito é o padrão ocidental). O elemento de maior contraste é a entrada; o segundo fica no caminho. Isso complementa a regra do olhar que já existe na doutrina (que cobre corte, não quadro). Medir: ordene blocos por contraste local; o vetor do 1º ao 2º não pode apontar para fora do quadro. [consenso de prática]

**C10. 9:16 não é 16:9 recortado.** Vertical: empilhe em 3 faixas (terço superior para contexto, centro para herói, terço inferior para apoio, tudo dentro da safe area que a doutrina já define), tipo maior em relação à largura (hero de 12 a 20% da largura do quadro em altura de letra), linhas de 12 a 18 caracteres. Horizontal: composição lateral, hero de 8 a 14% da altura. Medir: no vertical, razão altura/largura da caixa do conteúdo 1,2 ou mais; se for menor que 1, é layout horizontal espremido. Nota: a Envato registra que a regra "vertical primeiro" está cedendo a formatos mistos. [fonte da nota: https://elements.envato.com/learn/motion-design-trends; números inferência minha]

**C11. Profundidade em três planos com papéis.** Fundo (textura ou cor, sem informação), plano focal (informação), primeiro plano (elemento desfocado ou cortado que passa na frente, até 15% da área). A doutrina já dá os fatores de parallax; o que falta é exigir o primeiro plano. Medir: `depth_levels` 3 ou mais em cenas de câmera; primeiro plano com blur de 8 px ou mais. [consenso de prática]

**C12. Uma ideia por plano.** Se o plano precisa de dois títulos, são dois planos. Medir: 1 bloco no nível hero por frame; palavras na tela até 12 em plano de até 3 s. [fonte: https://youmind.com/landing/x-viral-articles/apple-product-video-design-secrets (opinião); limite de palavras inferência minha]

## 2. Tipografia em vídeo

**T1. Uma família, ou duas claramente distintas.** Display e corpo não precisam ser famílias diferentes; a amplitude de pesos e larguras de uma boa família basta (é o argumento da Buck para PP Formula no Comfy e do Google Fonts para superfamílias). Medir: famílias distintas no vídeo, 2 ou menos (mono para código real não conta). [fonte: https://buck.co/work/comfy-brand-refresh, https://fonts.google.com/knowledge/choosing_type/pairing_typefaces_within_a_family_superfamily, SKILL.md da Anthropic]

**T2. Pares por contraste de estrutura.** Par que funciona tem papel diferente e algo em comum (época, proporção, altura de x); duas sans parecidas no mesmo peso é o erro mais comum. Pares disponíveis no Google Fonts (existência conferida no pacote do Remotion; a escolha dos pares é minha):
- Instrument Serif (display) + Instrument Sans ou Geist (texto): editorial tech.
- Fraunces (eixos opsz, SOFT, WONK) + Hanken Grotesk: quente, com caráter.
- Newsreader ou Source Serif 4 (opsz) + Inter Tight: documentário.
- Bricolage Grotesque (opsz, wdth) sozinha: grotesca com personalidade, larguras variáveis.
- Geist + Geist Mono: linguagem Vercel; mono só em código e dado real.
- Archivo (eixo wdth 62 a 125) sozinha: do condensado ao expandido na mesma família.
- Roboto Flex ou Google Sans Flex (wdth, GRAD, opsz): para animar eixo.
- Mona Sans + Hubot Sans: par do GitHub, largura variável.
- Bodoni Moda ou Playfair (opsz) + DM Sans: alto contraste de traço, moda e luxo.
- Schibsted Grotesk, Familjen Grotesk, Host Grotesk, Funnel Display: alternativas a Inter com desenho próprio.
[fonte do critério: https://madegooddesigns.com/font-pairing-guide/ (guia de terceiro); lista inferência minha]

**T3. Fontes das marcas de referência e substitutas.** Stripe usa Söhne (Klim, paga), display em peso 300 segundo guia não oficial; OpenAI usa OpenAI Sans (ABC Dinamo, proprietária); Figma usa Figma Sans com corte condensado só em display; Vercel usa Geist e Geist Mono (livres); Linear usa Inter Variable com peso 510 e tracking negativo em display, segundo guias não oficiais. Substitutas livres: Söhne por Hanken Grotesk ou Schibsted Grotesk; OpenAI Sans por Geist ou Onest. [fonte: https://fontalternatives.com/inspiration/stripe-sohne/, https://designcompass.org/en/2025/02/06/openai-rebranding/, https://www.figma.com/blog/how-we-shaped-the-visual-identity-for-config-2025/, https://getdesign.md/design-md/vercel/preview.html; substitutas inferência minha]

**T4. Tracking varia com o tamanho, de forma contínua.** Quanto maior, mais apertado; quanto menor, mais aberto. A Apple removeu o degrau fixo aos 20 pt na SF: o tracking varia suavemente; cortes ópticos pequenos têm espaçamento mais aberto e altura de x maior. Vercel usa cerca de -0,05 em a 48 px (guia não oficial). Tabela de partida em 1080p: até 32 px, 0 a +0,01 em; 32 a 80 px, -0,01 em; 80 a 160 px, -0,02 a -0,03 em; acima de 160 px, -0,03 a -0,05 em. Aplicar: `letterSpacing = lerp por fontSize`, e `fontOpticalSizing: 'auto'` (ou `'opsz'` explícito) em fonte com eixo opsz. Medir: `letter-spacing` em em contra `font-size`; reprovar display acima de 120 px com tracking 0 ou positivo em caixa mista. [fonte do princípio: https://wwdcnotes.com/documentation/wwdc20-10175-the-details-of-ui-typography/ e https://fonts.google.com/knowledge/glossary/optical_size_axis; tabela inferência minha]

**T5. Caixa alta: menos de uma linha e com 5 a 12% de tracking a mais.** Butterick: caixa alta aceitável para menos de uma linha; some 5 a 12% de espaçamento. Em display gigante condensado o tracking positivo fica menor (0 a +2%), mas nunca negativo. Medir: bloco em caixa alta com mais de 1 linha ou mais de 24 caracteres = aviso; `letter-spacing` menor que 0 em caixa alta = erro. [fonte: https://practicaltypography.com/summary-of-key-rules.html; ajuste para display inferência minha]

**T6. Rótulo em caixa alta com tracking acima do título é assinatura de gerado.** Idem palavra do título em itálico, negrito ou cor só para "dar destaque", e marcador 01/02/03 fora de sequência real. Use só quando codifica informação. Medir: `caps_frac` até 20% dos blocos; padrão `^\d{2}$` ou `\d{2}/\d{2}` em texto de tela sem lista correspondente = aviso. [fonte: SKILL.md da Anthropic via https://capitalandcompute.net/blog/fix-ai-slop-design/]

**T7. Entrelinha por tamanho.** Corpo: 120 a 145% (Butterick). Display acima de 120 px: 0,90 a 1,05. Caixa alta sem descendentes: até 0,85, desde que os acentos não colidam (T12). Medir: `line-height / font-size` por bloco. [fonte do corpo: Butterick; display consenso de prática]

**T8. Comprimento de linha.** Página: 45 a 90 caracteres (Butterick), abaixo de 80 (skill da Anthropic). Vídeo não é página: display até 3 linhas de 8 a 20 caracteres; apoio até 2 linhas de 24 a 42 (a doutrina já fixa 32 a 42 para legenda). Quebra por sentido, nunca palavra órfã na última linha. Medir: caracteres por linha renderizada; última linha com 1 palavra de até 4 letras = aviso. [fonte: Butterick e SKILL.md; faixas de vídeo inferência minha]

**T9. Condensada não é corpo.** Fonte condensada (Anton, Bebas Neue, Big Shoulders, Barlow Condensed, League Gothic) só em display com até 3 palavras por linha. Em texto de apoio abaixo de 48 px a 1080p, ela fecha os contraformas e some no celular. Medir: família condensada (ou `wdth` abaixo de 85) em bloco com font-size abaixo de 48 px ou com mais de 20 caracteres = erro. [consenso de prática; limiar inferência minha]

**T10. Hierarquia em três níveis com razões.** Hero : apoio : metadado em torno de 9 : 2,5 : 1 (por exemplo 216, 60 e 24 px em 1080p), com peso invertido ao tamanho: hero grande pode ser leve (300 a 500), metadado pequeno precisa de 500 a 600. A doutrina atual manda 600 a 800 em todo título; hero leve em tamanho grande é o que Stripe e Apple fazem. Medir: `ratio_top2` e peso do maior texto; hero acima de 160 px com peso 800 ou mais em toda cena = monotonia de peso. [fonte parcial: Stripe em peso 300 no display, guia não oficial; razões inferência minha]

**T11. Tipografia variável como movimento de design.** Anime `wdth`, `wght`, `opsz` ou `GRAD` para mudar o estado da palavra. `GRAD` muda o peso sem mudar a largura, então não reflui a linha. Medir: `fontVariationSettings` animado só em fonte variável com o eixo presente. [fonte dos eixos: https://fontsource.org/fonts/google-sans-flex; uso inferência minha]

**T12. Português em caixa alta leva acento, til e cedilha.** A norma não dispensa acento em maiúscula (a busca só me devolveu a regra equivalente da RAE para o espanhol; a do português afirmo como norma conhecida, sem URL confirmada nesta pesquisa). Consequências: (1) confira que a fonte tem Á À Â Ã É Ê Í Ó Ô Õ Ú Ç; (2) entrelinha mínima de 1,05 em caixa alta com acento, senão o til colide com a linha de cima; (3) `overflow: hidden` de máscara de reveal precisa de `paddingTop` de 0,18 em ou mais, senão corta o acento; (4) `text-transform: uppercase` em vez de digitar em maiúscula, para manter a fonte de verdade acentuada. Medir: renderize "ÃÇÉÔ" na fonte e compare a caixa de tinta com a caixa da linha; teste de pixel na borda superior da máscara. [consenso de prática; números inferência minha]

**T13. Números tabulares e lining em todo dado.** `fontVariantNumeric: 'tabular-nums lining-nums'`, separador de milhar pt-BR, unidade em tamanho menor (50 a 60% do número) alinhada à linha de base. A doutrina já pede `tabular-nums` no contador; estenda a toda coluna de números. Medir: largura do bloco constante ao longo do contador. [consenso de prática]

**T14. Mono só para o que é código ou dado de máquina.** Mono em rótulo decorativo é "template chrome". Medir: `mono_frac` até 15%, e todo bloco mono precisa ser código, caminho, hash, horário ou valor. [fonte: SKILL.md da Anthropic]

## 3. Cor

**K1. Escolha cor em OKLCH, pela luminância.** Em HSL, o mesmo L dá luminosidades percebidas diferentes conforme o matiz; em OKLCH, `oklch(0.8 0.12 225)` e `oklch(0.8 0.12 100)` têm a mesma luminosidade percebida. Monte a paleta fixando L e C e girando h. Croma na prática fica abaixo de 0,37; o máximo depende de matiz e L. Aplicar: tokens em `oklch()`, converta para sRGB no build (o Chrome do Remotion aceita `oklch()` direto, **não verifiquei** nesta versão do template). Medir: converta cada pixel dominante para OKLCH. [fonte: https://evilmartians.com/chronicles/oklch-in-css-why-quit-rgb-hsl]

**K2. Escada de luminância antes do matiz.** Defina 4 a 6 cores nomeadas com papel: fundo, superfície, tinta, tinta secundária, acento, segundo acento opcional. Passos de L: fundo e tinta com diferença de 0,60 ou mais; superfície a 0,04 a 0,08 do fundo; tinta secundária a 0,25 a 0,35 da tinta. Fundo com L de 0,87 ou mais aceita texto preto com bom contraste. OKLCH sozinho não mede contraste: use APCA ou WCAG (a doutrina já exige AA). Medir: histograma de L do frame com 3 picos separados. [fonte: Evil Martians para o 0,87 e para APCA; SKILL.md para "4 a 6 cores nomeadas"; passos inferência minha]

**K3. 60-30-10 medido em área.** Dominante 55 a 70%, secundária 20 a 35%, acento 3 a 10%. Acento acima de 15% deixa de ser acento. Medir: `n_colors_2pct` entre 3 e 5 e a área de cada cluster. Exatamente 2 clusters em toda cena é o "duas cores chapadas" que esta referência existe para evitar. [consenso de prática]

**K4. Sistemas restritos que funcionam em vídeo.**
- Duas cores por peça, trocando o par a cada peça: a Buck limitou cada asset do In Motion a duas cores, com azul elétrico no centro do sistema. Vale se o par muda entre cenas.
- Paleta por tema: Figma Config guarda uma paleta por trilha em variáveis e casa o fundo da foto do palestrante com ela.
- Tons escuros para mudança de humor mais um toque da cor da marca: Linetest para Home Depot.
- Fundo preto ou branco com um elemento saturado, sem saturado sobre saturado: leitura dos filmes da Apple.
[fonte: https://type-01.com/?p=34730, https://www.figma.com/blog/how-we-shaped-the-visual-identity-for-config-2025/, https://www.stashmedia.tv/?p=82132, https://youmind.com/landing/x-viral-articles/apple-product-video-design-secrets]

**K5. Triádico restrito: três matizes, um só saturado.** h separados em cerca de 120 graus, mesmo L (por exemplo 0,72), um com C 0,16 a 0,20 e os outros dois com C 0,04 a 0,08. Medir: 3 clusters de matiz, só um com C acima de 0,12. [inferência minha]

**K6. Cor como significado, com lei por cena.** A `law` do `direction.json` já existe. Acrescente: cada cor de acento tem no máximo um significado e aparece em até 40% das cenas; cor que aparece em toda cena é fundo. Medir: presença do acento por cena. [inferência minha]

**K7. Como sair do "preto + neon".** (a) Quadro claro: no estudo da Advids, quadros claros foram de 21 em 60 (35%) no 1º trimestre de 2026 para 22 em 40 (55%) de abril a agosto, e o brilho médio mediano subiu de 117 para 154 em 255. (b) Paleta tirada do assunto: tinta de recibo, verde de quadra, cor da UI real. (c) Gradiente mesh só na faixa superior, como a Stripe (creme, laranja, lavanda, índigo, rosa), não tela cheia. (d) Fotografia como fonte de cor (OpenAI: paisagem e natureza morta com padrões do Sora, base de cinzas e azuis com primárias de contraste). (e) Não troque um padrão por outro: creme perto de #F4F1EA com terracota perto de #D97757 também é cluster de gerado, assim como quase preto tingido (#0B0B0B, #111) no lugar de preto. Medir: reprovar par {L do fundo abaixo de 0,2 mais um único cluster com C acima de 0,2} quando não vem do `brand.json`. [fonte: https://advids.co/blog/ui-animation-motion-design-trends, https://fontalternatives.com/inspiration/stripe-sohne/ (não oficial), https://designcompass.org/en/2025/02/06/openai-rebranding/, SKILL.md da Anthropic]

**K8. Gradiente interpolado em oklab.** `linear-gradient(in oklab, a, b)` evita o meio acinzentado do sRGB. Some ao que a doutrina já diz sobre banding: grão por cima. [fonte: Evil Martians]

**K9. Grade (color grade) unifica o que foi feito separado.** Aplique uma só transformação no fim, sobre gráfico e imagem real juntos: curva com pretos levantados para L 0,04 a 0,08, altas luzes seguradas em 0,96, leve separação de temperatura entre sombra e luz. `@remotion/effects` tem `lut()` (já citado em `techniques-advanced.md`). Medir: mínimo e máximo de L do frame; preto puro 0 e branco puro 1 no mesmo frame denunciam gráfico sem grade sobre foto. [consenso de prática; valores inferência minha]

**K10. Textura com valores (somando ao que já existe: grão 4 a 10%, halation, bloom).**
- Papel: textura em `multiply` a 8 a 20%, fundo com L 0,93 a 0,96 e C 0,01 a 0,02.
- Halftone: passo do ponto de 6 a 12 px em 1080p, ângulo de 45 graus em uma cor, 15 e 75 em duas. SVG `<pattern>` com raio vindo da luminância, ou `radial-gradient` repetido mais `contrast()`.
- Dither: a Figma fez ferramenta própria para pontilhar centenas de retratos no Config 2026. Bayer 4x4 ou 8x8 a 1/3 da resolução e ampliação com `image-rendering: pixelated`.
- Riso: 2 ou 3 tintas spot em `multiply`, desregistro de 1 a 3 px entre tintas, grão só dentro da tinta (Config 2025 usou riso por causa da imperfeição).
- Ruído em gradiente: `feTurbulence` com `baseFrequency` 0,6 a 0,9 em `overlay` a 6 a 12%.
- Luz volumétrica: gradiente radial em `screen` a 10 a 25% mais ruído de baixa frequência (0,005 a 0,02) como máscara.
- Taxa de quadro como textura: a Figma baixou o filme de abertura do Config 2025 de 60 para 15 fps para parecer feito à mão. Em 30 fps, `stepped(frame, 2)` na camada ilustrada.
Medir: `grain_sigma` acima de zero em área chapada e igual entre camada gráfica e foto. [fonte: posts da Figma sobre Config 2025 e 2026; valores numéricos consenso de prática ou inferência minha]

## 4. Linguagem de estúdio

O que cada fonte de fato sustenta. Onde diz "inferência", é o que eu conheço do trabalho, sem texto que confirme.

| Estúdio ou marca | Traços reproduzíveis | Origem |
|---|---|---|
| Buck | (1) Conteúdo sempre dentro de contêineres de canto misto (curvo e angular) que conectam, separam, expandem e se reorganizam; imagem entra mascarada pelo contêiner. (2) Uma família com muitos pesos e larguras (PP Formula) em vez de duas famílias. (3) Sistema de duas cores por asset, com uma cor central. | https://buck.co/work/comfy-brand-refresh, https://type-01.com/?p=34730 |
| Ordinary Folk | (1) Uma paleta única compartilhada por todos os quadros, com color script da peça inteira. (2) Progressão de complexidade visual ao longo do filme, não montagem de planos desconexos. (3) 3D estilizado misturado a 2D chapado. Grade geométrica rígida e textura fina de grão dentro das formas: inferência minha. | https://motionographer.com/2019/09/16/join-the-movement/ |
| Gunner | (1) Cel por cima de referência 3D (animador desenha sobre o 3D). (2) Movimento em twos com câmera contínua: inferência minha, compatível com `stepped` já existente. | https://motionographer.com/2016/12/12/gunner-their-new-film-mesh-and-the-importance-of-changing-things-up/ (só resumo de busca) |
| Oddfellows | (1) Formas simples com movimento orgânico para aquecer produto digital. (2) Cel e motion convivendo com filmagem de produto real. | https://dev.motionographer.com/2015/10/13/oddfellows-works-with-nest/, https://motionarray.com/blog/industry-spotlight-oddfellows (403, só resumo de busca) |
| ManvsMachine | (1) Cada plano é uma metáfora de material, classificada por propriedade (macio e amortecido, leve e respirável). (2) Produto escaneado em 3D para fidelidade. (3) Objeto físico construído e filmado quando o gráfico ficaria frio. | https://www.stashmedia.tv/manvsmachine-nike-air-max-2017/, https://maxon.net/en/article/man-vs-machine-fusing-creativity-with-technology-with-the-help-of-cinema-4d |
| Giant Ant | (1) Textura de pincel e hachura cruzada dentro das formas. (2) Composições fragmentadas. (3) 3D com cara de massinha (faux claymation), cortes e câmera de cinema. | https://motionographer.com/?p=64478, https://motionographer.com/2016/08/26/another-great-film-for-slack-from-canadas-very-own-giant-ant/ |
| Golden Wolf | (1) Recusa do movimento mais liso: "bold and edgy". (2) Gráfico retrô e sujo misturando 2D e 3D. Traço grosso e smear: inferência minha, a fonte não descreve. | https://goldenwolf.tv/culture/artist-spotlight-stephanie-mercier, https://motionographer.com/2025/05/12/studio-stories-12-years-of-golden-wolf/ |
| Linetest | (1) Cel feito à mão a serviço de personagem. (2) Paleta escura para marcar mudança de humor, com toques pequenos da cor da marca. | https://www.stashmedia.tv/?p=82132 |
| Hornet | (1) Stop motion, ilustração, CG e composição no mesmo plano. (2) Adereços fabricados à mão (papel, origami, tecido) e luz feita na câmera. Fontes de 2005 a 2020. | https://www.dragonframe.com/blog/tactile-animation-for-st-louis-childrens-hospital/ |
| Apple | (1) Uma ideia por plano e muito vazio. (2) Fundo preto ou branco com um elemento em cor forte. (3) Cortes que não se notam, SFX raros. MacBook Pro M5: 79 cenas em 100 s, sem narração, pessoas antes do produto. | https://youmind.com/landing/x-viral-articles/apple-product-video-design-secrets (opinião), https://videngineer.com/teardowns/launch/apple-macbook-pro-m5-launch-film-teardown/ (método não declarado) |
| Linear | (1) Sem narração; 33 s, cerca de 20 cenas por minuto, 2 trocas de música. (2) Vinheta que escurece a periferia e isola a tela central. (3) Sistema estático: quase preto, hierarquia por opacidade de branco, Inter em peso 510, tracking negativo em display. | https://videngineer.com/teardowns/motion-graphics/linear-introducing-linear-for-agents/, https://advids.co/blog/saas-product-launch-videos (n=7), https://getdesign.md (não oficial) |
| Stripe | (1) Filme do Reader: 52 s, sem narração, 58% de cenas em 3D animado, magenta e ciano, arco problema, solução, personalização, integração. (2) Display em peso leve (300). (3) Mesh gradient restrito ao terço superior. | https://videngineer.com/teardowns/launch/stripe-introducing-stripe-reader/, https://fontalternatives.com/inspiration/stripe-sohne/ |
| Vercel | (1) UI no segundo zero (a interface é o gancho). (2) Final com zoom out da UI até virar o logo. (3) Tinta #171717, não preto puro; Geist com tracking apertado e Geist Mono em rótulo técnico; borda de 1 px feita com sombra. | https://advids.co/blog/saas-product-launch-videos (n=7), https://getdesign.md/design-md/vercel/preview.html (não oficial) |
| Figma | (1) Glifos feitos de primitivas com elemento interno e externo que reagem um ao outro; cantos alternando redondo e vivo. (2) Filme de abertura a 15 fps; movimento de tipo expressivo mais longo, de tipo funcional mais curto. (3) Config 2026: dither, rabisco, gradiente borrado e partícula oval em colagem. Sizzle do Config 2025: 81 s, 57,7 cenas por minuto, 71% captura de tela, 78% com texto sobreposto. | posts da Figma; https://videngineer.com/teardowns/launch/figma-all-launches-config-2025/ |
| OpenAI | (1) "O ponto" (círculo preto, o cursor) como base da grade e presente nas letras. (2) Base de cinzas e azuis com primárias de contraste. (3) Fotografia de paisagem e natureza morta com padrões gerados. Motion com Studio Dumbar, sem detalhe publicado. | https://designcompass.org/en/2025/02/06/openai-rebranding/, https://www.creativereview.co.uk/openai-brand-refresh/ |
| Arc | (1) Cartões flutuantes tirados da moldura do navegador. (2) Tarefa acelerada a 300%. (3) Corte seco do estado de sucesso para texto de chamada. **Não achei nada** sobre a direção de arte dos filmes. | https://advids.co/blog/saas-product-launch-videos (n=7, sem método) |

Regras que saem da tabela:

**E1. Contêiner como unidade.** Toda imagem e toda UI entram dentro de uma forma com geometria própria da marca (`clipPath` ou `mask`), e a forma participa da transição. Medir: imagem com bounding box retangular igual ao quadro em mais de metade das cenas = não há sistema. [fonte: Buck Comfy]

**E2. Um motivo com parte interna e externa.** O motivo do `direction.json` ganha duas partes que reagem com atraso (`lag` de 2 a 4 frames). [fonte: Figma Config 2025]

**E3. Imperfeição de processo declarada.** Uma só por peça: 12 ou 15 fps na camada ilustrada, desregistro de riso, dither ou borda de recorte. Medir: `stepped` presente, ou deslocamento entre canais. [fonte: Figma Config 2025 e 2026; Envato "craft as luxury"]

**E4. Color script.** Uma faixa com a cor dominante de cada cena, aprovada antes de animar; a cena de clímax tem a maior distância de cor em relação à anterior. Medir: ΔE_OK do cluster dominante entre cenas vizinhas; todas abaixo de 0,05 = peça sem arco de cor. [fonte: Ordinary Folk; métrica inferência minha]

## 5. Filme de lançamento de 60 a 90 s (2025 e 2026)

**L1. Duração.** Mediana de 1:14 (1º tri 2026) e 1:18 (abr a ago 2026) em 100 vídeos de software; metade central de 0:50 a 1:45. Filmes de marca de ponta são mais curtos: Linear 33 s, Anthropic Opus 4.6 39 s, Stripe Reader 52 s, Notion AI 57 s, Figma Motion 1:09, Cursor 2.0 1:04. [fonte: Advids; videngineer; https://www.moonb.io/blog/product-launch-video]

**L2. Ritmo de corte: dois regimes.** O vídeo B2B típico tem mediana de 8,4 a 8,6 mudanças de cena por minuto (cerca de 7 s por cena). Os filmes de referência têm 20 a 58 cenas por minuto: Linear 20,2; Anthropic 21,3; Notion 29,7; Apple cerca de 47 (79 em 100 s); Figma 57,7. Ou seja, 1 a 3 s por plano. As duas fontes medem "cena" de formas diferentes e o método do videngineer não é declarado. Aplicar: alvo de 20 a 30 cenas por minuto num filme de marca, com 2 ou 3 planos longos (4 a 6 s) de respiro, o que respeita a regra 3x da doutrina. Medir: `timeline.json`, cenas por minuto. [fonte: Advids e videngineer; alvo inferência minha]

**L3. Sem narração nos filmes de referência.** As cinco prévias que li (Linear, Notion, Anthropic, Apple, Figma, Stripe são seis) dizem "sem narração; a história é levada por corte e som". No conjunto geral ocorre o oposto: mediana de palavras faladas subiu de 65 para 101. Legenda queimada cresceu de 2 em 60 para 7 em 40. Aplicar: a opção sem voz deve ser a padrão para filme de marca, com o texto de tela como roteiro (a `direction.md` já cobre "funcionar sem som"). [fonte: videngineer, Advids]

**L4. Quando a UI aparece.** Mediana do primeiro frame de interface: 0:13 (1º tri) e 0:18 (abr a ago). Em n=7 marcas de ponta: 5 cortam para a UI antes de 3 s depois de uma frase de dor, 2 abrem dentro da UI. Cobertura mediana de UI no tempo total: 33 a 39%. Aplicar: UI real até os 3 s, ou gancho tipográfico de até 3 s e UI logo depois. [fonte: Advids, os dois textos]

**L5. UI real, recortada.** Captura de tela subiu de 22 em 60 (37%) para 25 em 40 (63%); motion graphics puro caiu de 68% para 48%. Em n=7, 6 mostram a UI "abstraída" (sem bordas nativas, só o painel do recurso) e 6 desfocam o fundo quando abre um modal. Aplicar: recrie a UI em React ou use captura, corte para o painel, tire a moldura do navegador, blur de 8 a 20 px no resto. [fonte: Advids]

**L6. 3D em queda no software, forte em hardware.** 3D na construção caiu de 14 em 60 (23%) para 5 em 40 (13%); como técnica principal, de 10 para 2. No filme do Stripe Reader (hardware), 58% das cenas são 3D. Aplicar: 3D só quando há objeto físico ou metáfora de material; não como enfeite de SaaS. [fonte: Advids, videngineer]

**L7. Tipografia cinética é pontuação, não o filme.** Presente em 53 a 63% dos vídeos, mas ocupa mediana de 20 a 25% do tempo; vídeos em que ela cobre metade do tempo caíram de 7 para 1. Medir: fração do tempo em cenas só de texto, até 30%. [fonte: Advids]

**L8. Tempo comprimido.** 7 de 7 aceleram a tarefa; 5 de 7 usam indicador de progresso hiperacelerado; Arc acelera a 300%; Raycast corta entre teclas pulando carregamento. Aplicar: `timeRemap` já existe; nunca mostre espera real. [fonte: Advids n=7]

**L9. Estado de sucesso desenhado.** Toast vindo do topo em 4 de 7; animação local (círculo que fecha, confete) em 3 de 7. Um por recurso. [fonte: Advids n=7]

**L10. Fecho.** 5 de 7 fazem transição fluida da UI para o logo (Vercel: zoom out até a UI virar o logo); 2 de 7 cortam seco para texto. [fonte: Advids n=7]

**L11. Batidas para 60 a 90 s** (síntese minha das fontes acima, compatível com a tabela de `direction.md`):
- 0 a 3 s: gancho, uma frase de dor ou a UI em ação.
- 3 a 12 s: o produto inteiro num plano largo, nome.
- 12 a 55 s: 3 recursos, cada um com 8 a 14 s em 4 a 6 planos (contexto, close no painel, ação acelerada, sucesso).
- 55 a 70 s: montagem rápida de tudo (1 s por plano).
- últimos 5 a 8 s: marca, uma linha, onde encontrar.
[inferência minha]

**L12. Macro.** Close extremo de material ou de pixel (texto da UI a 300 a 600% com profundidade de campo) como plano de respiro entre recursos; o som acompanha a escala (ver S5). Não achei fonte que quantifique macro em filme de produto. [inferência minha]

## 6. Motion sobre imagem real

**F1. Ken Burns com número.** Não existe padrão documentado; as fontes só dão faixa de escala (100 a 200%) e dizem que a duração define a velocidade. Recomendação: 3 a 8% de escala em 4 a 6 s (1 a 2% por segundo), sempre em direção ao assunto ou saindo dele, nunca os dois no mesmo plano; movimento já em curso no primeiro frame e ainda em curso no último (o corte cai no meio); curva linear ou quase; fonte com pelo menos 1,2x a resolução final no maior zoom (zoom de 200% em 1080p pede imagem 3840x2160). Medir: escala final/inicial e resolução da imagem. [fonte do requisito de resolução: https://www.sliderrevolution.com/documentation/pan-zoom/ e https://larryjordan.com/articles/final-cut-pro-x-create-a-ken-burns-effect/; taxas inferência minha]

**F2. Parallax 2.5D de foto.** Recorte o assunto (`roto.py --backend rembg` num quadro), preencha o fundo atrás dele, 3 camadas. Fundo de 1,00 para 1,03, assunto de 1,00 para 1,08, primeiro plano de 1,00 para 1,15, mais deslocamento lateral de 1 a 2% do quadro; blur de 2 a 6 px no fundo. Medir: razão de escala entre camadas de 1,03 ou mais; borda do recorte com pena de 1 a 2 px. [consenso de prática]

**F3. Duotone de verdade.** Mapeie a luminância para duas tintas (sombra e luz) em vez de pôr cor em `multiply` sobre foto colorida: `feColorMatrix` para cinza e `feComponentTransfer` com `tableValues` das duas cores, ou `grayscale(1) contrast(1.1)` com camada `mix-blend-mode: lighten` e outra `darken`. Sombra com L 0,15 a 0,25, luz com L 0,85 a 0,95, matizes a 60 graus ou mais um do outro. Medir: pixels da foto sobre a reta entre as duas cores em OKLab. [consenso de prática; valores inferência minha]

**F4. Recorte com intenção.** Recorte de colagem tem borda visível (traço de papel de 4 a 10 px, sombra curta de 2 a 6 px com deslocamento numa só direção) ou é perfeito; meio-termo denuncia. [consenso de prática; tendência de papel rasgado em https://blog.videobolt.net/post/top-motion-graphics-trends-2026]

**F5. Vídeo dentro da letra.** Altura da letra de 35% do quadro ou mais, peso 800 ou mais, até 6 caracteres por linha, e o vídeo interno com movimento lento e contraste alto, senão a letra some. `background-clip: text` ou `<mask>` de SVG com `<Video>` atrás. Medir: área de tinta do texto de 25% do quadro ou mais. [inferência minha]

**F6. Texto preso à cena.** Perspectiva casada (`matrix3d` a partir de 4 pontos), blur de movimento igual ao da filmagem, e o texto passa atrás do assunto quando possível. Texto que flutua sem tremer junto com a câmera é o defeito número um. `techniques-3d-compositing.md` cobre o como (`track.py`, `<CornerPin>`, `roto.py`). [consenso de prática]

**F7. Integração de gráfico e filmagem.**
- Preto e branco do gráfico tirados da filmagem: amostre o ponto preto e o ponto branco do plano e use como limites; nunca #000 e #FFF sobre vídeo.
- Grão por cima de tudo, depois do gráfico: o ruído aparece mais nas sombras, então grão e nível de preto se conferem juntos.
- Nitidez e saturação casadas: gráfico vetorial leva blur de 0,3 a 0,6 px sobre filmagem 1080p.
- Light wrap: fundo borrado em 20 a 60 px aplicado na borda do elemento em `screen`.
- Sombra na direção da luz da cena, uma só direção.
Medir: `grain_sigma` igual nas duas regiões; mínimo de L do gráfico de pelo menos o mínimo de L da filmagem. [fonte: https://vitrina.ai/blog/advanced-compositing-techniques-seamless-vfx-integration/ e https://nofilmschool.com/2015/03/basic-tips-make-after-effects-compositing-look-better; blur de 0,3 a 0,6 px inferência minha]

**F8. Split screen e moldura.** Calha constante (0 ou 8 a 16 px, nunca valores diferentes na mesma cena), linha de horizonte e escala do assunto casadas entre painéis, raio de canto único. Moldura: a foto ocupa 60 a 75% do quadro, com margem assimétrica (C6). [inferência minha]

**F9. Erros que denunciam amador.** Foto de banco sem tratamento (a doutrina já proíbe ícone de banco); foto esticada ou com resolução abaixo do zoom; tipografia branca pura sobre foto sem gradiente de proteção (use degradê de 0 a 60% de preto só atrás do texto, não na foto inteira); sombra projetada genérica; recorte com halo; grão só no gráfico ou só na foto; Ken Burns que para e volta. [consenso de prática]

## 7. Som

A `audio.md` já cobre licença, níveis, ducking e loudness. O que estúdio faz de diferente, segundo Wes Slover e Trevor (Sono Sanctus):

**S1. SFX afinado no tom da música.** Sons com altura definida ao lado de música precisam estar no tom; em varredura descendente, só a nota inicial precisa encaixar. Aplicar: `sfx.py` recebe a tônica da trilha e gera pop, tick e shimmer nessa nota ou na quinta. Medir: altura fundamental do SFX contra o tom detectado da trilha. [fonte: https://www.schoolofmotion.com/blog/sono-sanctus-podcast-podcast]

**S2. Poucos pontos de sincronia exatos; o resto fica abstrato sob a música.** Escolha de 3 a 6 momentos por 30 s para acertar no frame. Isso reforça o "um SFX por evento com significado" que já existe. [fonte: mesma]

**S3. Tirar em vez de pôr.** No ajuste final, quase tudo foi abaixar; o design de som ocupa menos espaço quando a música entra. Medir: densidade de SFX por 10 s cai quando a trilha está acima de -18 dB. [fonte: mesma]

**S4. SFX com a mesma textura da trilha.** Sons feitos dos mesmos timbres da música se misturam e fazem a música parecer que responde à imagem. Biblioteca usada como matéria-prima em camadas, não solta como veio. [fonte: mesma]

**S5. Escala do som igual à escala da imagem.** Close extremo pede som gravado de perto e maior que a vida (lápis em papelão em vez de papel, para ter peso). Impacto: bumbo grande mais booms por baixo, e uma cauda com delay e reverb que leva o plano embora. [fonte: mesma]

**S6. Camadas de um whoosh.** Varredura de ruído de banda larga (ar), elemento tonal (corpo), gravação com textura (grão). Separe som de movimento de objeto e som de troca de cena. [fonte: https://sonilo.com/ai-music/whoosh-sound-effect-guide, via resumo de busca]

**S7. Do real ao surreal.** O som começa realista e fica abstrato junto com a imagem; a música só entra depois da primeira batida realista. Num filme de lançamento: foley de UI seco nos primeiros 3 s, trilha entra no plano do produto. [fonte: Sono Sanctus; aplicação a lançamento inferência minha]

**S8. Trocas de música como estrutura.** Linear tem 2 trocas em 33 s, Notion 5 em 57 s, Anthropic uma cama contínua em 39 s. Aplicar: uma mudança de seção da trilha por ato, casada com o color script (E4). [fonte: videngineer; aplicação inferência minha]

**S9. Conferir em alto-falante de celular.** Fone exagera detalhes e engana no nível da voz; sem bom alto-falante a tendência é exagerar o grave. Medir: energia abaixo de 120 Hz não pode carregar informação (o sub some no celular); cheque o mix com passa-alta em 150 Hz. [fonte: Sono Sanctus; corte de 150 Hz inferência minha]

## 8. Tendências 2025 e 2026, e o que virou clichê

Tendências com fonte (todas de fornecedores de template ou asset, não de crítica independente):

- Feito à mão e imperfeito: traço solto, contorno irregular, frame a frame. [VideoBolt; Envato "craft as luxury", com Hermès como exemplo]
- Textura analógica: grão, fibra de papel, poeira, VHS, luz de tungstênio, tipografia vintage. [VideoBolt; Envato]
- Papel rasgado e colagem, com taxa de quadro reduzida. [VideoBolt]
- Layout modular editorial: quadros, recortes, blocos de tipo em sequência. [VideoBolt]
- Híbrido 2D e 3D; 3D estilizado, mascote "de brinquedo", diorama, cel shading. [VideoBolt; Envato 3D]
- Vidro e dispersão, ligado ao Liquid Glass da Apple; a própria fonte chama de linguagem que volta. [VideoBolt]
- Motion por código: procedural, ASCII, física 2D reativa, partículas. [Envato]
- Filme de marca com história em vez de visual rápido e chamativo; edição minimalista, planos longos. [Envato, os dois textos]
- Fim da regra de proporção única; formatos mistos. [Envato]
- Interface capturada no lugar de interface desenhada, quadro claro, mais fala. [Advids, com contagem]
- Motion como função dentro de produto; gosto como diferencial com IA barateando o polimento. [School of Motion, recap de 2025]

Clichê a evitar (o que as fontes dizem estar cansado, mais o que os catálogos de "AI slop" listam):

- "Visual rápido e chamativo" de anúncio e transição dramática. [Envato]
- Polimento liso e "mesmice generativa". [Envato; VideoBolt]
- Retângulo arredondado como molde único de app. [School of Motion]
- Gradiente índigo para roxo, vidro fosco e glow sem função, três cartões iguais, contador que sobe em toda estatística, fade com subida em toda seção. [capitalandcompute; 925studios]
- Quase preto com um neon; creme com serifada e terracota; fio fino com canto zero e colunas de jornal; rótulo em caixa alta com tracking; mono em rótulo. [SKILL.md da Anthropic]
- Atenção: grão, VHS e papel rasgado estão em todo pacote de template de 2026 (os exemplos da VideoBolt são templates à venda). Textura analógica aplicada por cima de layout genérico já é o próximo clichê. [inferência minha]

## 9. Sinais de "feito por IA ou template" em design, com antídoto

| Sinal | Antídoto | Medida |
|---|---|---|
| Condensada gigante à esquerda em toda cena | Variar o nível do hero: em pelo menos 1/3 das cenas o herói é imagem, UI ou forma, não texto (C3, T10) | fração de cenas com o maior elemento sendo texto, até 60% |
| Duas cores chapadas (quase preto e um acento) | Paleta de 4 a 6 cores com papel, tirada do assunto; quadro claro (K2, K7) | `n_colors_2pct` de 3 a 5; reprovar par fundo L<0,2 mais 1 cluster C>0,2 |
| Contador ou rótulo mono no canto | Mono só para código e dado de máquina (T14) | `mono_frac` até 15% |
| Rótulo em caixa alta com tracking acima do título | Remover, ou deixar só o que codifica informação (T6) | `caps_frac` até 20% |
| Marcador 01/02/03, "A · B · C", seta em tudo | Só em sequência real | regex no texto de tela |
| Uma palavra do título em cor, itálico ou negrito | Ênfase por escala ou posição, uma vez por peça | spans de estilo diferente dentro do hero |
| Número grande, rótulo pequeno, stats de apoio | Dado dentro do contexto (gráfico, recibo, UI real) | cena com 1 número de 200 px ou mais e 2 a 4 textos pequenos alinhados |
| Tudo com o mesmo raio e a mesma sombra | Raio e elevação por hierarquia; no máximo 2 raios | valores distintos de `border-radius` e `box-shadow` |
| Grade de 3 cartões iguais | Assimetria: 1 grande e 2 pequenos, ou lista | caixas de mesmo tamanho lado a lado, 3 ou mais |
| Tudo centralizado ou tudo na margem esquerda | Alternar eixo por cena (C1, C3) | desvio padrão de `mass_offset` entre cenas de 0,05 ou mais |
| Gradiente decorativo, glow, vidro fosco | Uma textura com processo declarado (E3) | já coberto em `direction.md`, sem medida confiável |
| Ícone de linha fina genérico | Desenhar o ícone com a forma do motivo, ou usar o objeto real | sem medida |
| Texto vago ("Mais rápido. Mais simples.") e número inventado | Frase que só este produto diria; a doutrina já proíbe dado inventado | revisão |
| Foto de banco sem tratamento | Duotone, recorte ou grade (F3, F4, K9) | pixels da foto fora da paleta |
| Textura por cima de layout genérico | Textura só depois de o quadro sem textura passar | comparar `layout.py` com e sem a camada |

Origem dos sinais: SKILL.md da Anthropic, capitalandcompute, 925studios, wiki do ux-skill (só resumo de busca). A adaptação para frame de vídeo e as medidas são inferência minha. A regra geral das três fontes: trocar um padrão por outro não funciona; escreva a direção antes do código (4 a 6 hex, 1 ou 2 famílias, um conceito de layout) e ponha um verificador que falha.

---

## (a) As 15 regras que mais mudam o resultado, em ordem

1. **Direção derivada do assunto, com 4 a 6 cores nomeadas e 1 ou 2 famílias**, e reprovação dos cinco clusters padrão (K7, seção 9).
2. **O herói nem sempre é texto**: em 1/3 das cenas ou mais é imagem, UI real ou forma (seção 9, L5).
3. **`n_colors_2pct` entre 3 e 5 e 60-30-10 por área** (K3).
4. **Salto de escala de 3:1 ou mais e no máximo 4 tamanhos por frame** (C7).
5. **Hero leve em tamanho grande, metadado pequeno e firme**; nada de 800 em tudo (T10).
6. **`mass_offset` variando entre cenas** e vazio assimétrico (C3, C6).
7. **Espaço negativo com faixa por tipo de quadro** (C5).
8. **Contêiner com geometria da marca para toda imagem e UI** (E1).
9. **Uma imperfeição de processo declarada**, depois de o quadro limpo passar (E3, K10).
10. **Paleta em OKLCH com escada de L e color script entre cenas** (K1, K2, E4).
11. **Tracking contínuo por tamanho e caixa alta só com tracking positivo e menos de uma linha** (T4, T5).
12. **Mono, caixa alta com tracking e marcador numérico só quando codificam informação** (T6, T14).
13. **UI real recortada até os 3 s, tempo comprimido, estado de sucesso desenhado** (L4, L5, L8, L9).
14. **Filme de marca sem narração, 20 a 30 cenas por minuto com 2 ou 3 planos longos** (L2, L3).
15. **Grade final única e grão por cima de gráfico e foto juntos; preto e branco amostrados da imagem** (K9, F7).

## (b) Seis direções de arte

Paletas em OKLCH são propostas minhas, para ajustar à marca. Nenhuma é condensada gigante em duas cores.

**1. Mesa de montagem** (colagem editorial)
- Grade: 12 colunas quebradas de propósito; recortes girados de 2 a 6 graus, sobrepostos, 2 ou 3 sangrando.
- Tipografia: Fraunces (opsz alto) em caixa mista, 120 a 200 px, com Hanken Grotesk a 28 a 36 px.
- Paleta: papel `oklch(0.95 0.015 90)`, tinta `oklch(0.22 0.02 260)`, três tintas spot em L 0,70: `oklch(0.70 0.17 30)`, `oklch(0.70 0.12 150)`, `oklch(0.70 0.13 250)`.
- Textura: papel em multiply a 15%, borda de recorte de 6 px, sombra curta, fita.
- Movimento dominante: `stepped(frame, 2)` na camada de colagem com câmera contínua; peças entram por corte e deslize curto.
- Referência: identidade do Config 2026 da Figma. https://figma.com/blog/the-visual-identity-behind-config-2026

**2. Sistema de primitivas** (geometria que se reorganiza)
- Grade: modular 8 x 8; tudo é círculo, quadrado, meia-lua, com cantos alternando redondo e vivo.
- Tipografia: uma família de largura variável (Archivo ou Mona Sans), peso 400 a 500, hero de 96 a 140 px. Tipo médio, forma grande.
- Paleta: 4 cores em L 0,75 e C 0,14 (h 25, 95, 160, 265) sobre `oklch(0.97 0 0)`, tinta `oklch(0.20 0 0)`.
- Textura: nenhuma, ou riso (multiply e desregistro de 2 px).
- Movimento dominante: formas conectam, dividem, expandem e viram máscara do conteúdo (`interpolatePaths`, `IrisReveal`).
- Referência: Buck para Comfy; glifos do Config 2025. https://buck.co/work/comfy-brand-refresh

**3. Estúdio de produto** (macro e material)
- Grade: um objeto, centro deslocado para um terço; `empty_frac` de 70 a 80%.
- Tipografia: Geist ou Onest em peso 300 a 400, 48 a 72 px, uma linha por plano, pequena em relação ao quadro.
- Paleta: fundo neutro contínuo `oklch(0.16 0.005 260)` ou `oklch(0.96 0.003 90)`, uma cor forte só no objeto.
- Textura: luz volumétrica, profundidade de campo, grão a 4%.
- Movimento dominante: câmera lenta em órbita ou push, cortes invisíveis, close extremo de material.
- Referência: ManvsMachine para Nike Air Max 2017; filmes de produto da Apple. https://www.stashmedia.tv/manvsmachine-nike-air-max-2017/

**4. UI como paisagem** (claro)
- Grade: a UI real é o cenário; painéis recortados sem moldura, inclinados em 3D sobre a diagonal (C4), 3 planos de profundidade.
- Tipografia: a fonte do próprio produto, 500, 56 a 88 px, legenda curta ao lado do painel. Mono só no código real.
- Paleta: tirada da UI pelo `brand.json`; fundo claro `oklch(0.97 0.004 250)`, superfícies a 0,04 de L, a cor do produto só no estado ativo.
- Textura: blur de fundo quando abre modal, sombra longa e suave numa direção, vinheta leve.
- Movimento dominante: câmera que viaja de painel em painel, cursor em arco, tempo acelerado, fecho em zoom out até o logo.
- Referência: Linear for Agents; Vercel. https://videngineer.com/teardowns/motion-graphics/linear-introducing-linear-for-agents/

**5. Editorial fotográfico**
- Grade: foto sangrada em 2/3 do quadro mais coluna de texto em 1/3; alterna com foto emoldurada a 65% e margem assimétrica.
- Tipografia: Instrument Serif ou Newsreader (opsz) em 90 a 150 px, caixa mista, com Instrument Sans a 28 a 34 px.
- Paleta: duotone por ato (sombra `oklch(0.20 0.05 265)`, luz `oklch(0.92 0.04 85)`), um acento da marca até 5% da área.
- Textura: grão a 6% por cima de tudo, halation leve, grade única.
- Movimento dominante: Ken Burns lento (F1), parallax 2.5D (F2), texto por máscara de linha.
- Referência: imagem de marca da OpenAI em 2025; tendência de filme de marca com história. https://designcompass.org/en/2025/02/06/openai-rebranding/

**6. Retícula e código** (dither, halftone, generativo)
- Grade: célula fixa de 8 ou 16 px que tudo respeita, de imagem a texto.
- Tipografia: Geist Mono ou Martian Mono como voz principal (aqui o mono é o conceito, não enfeite), com Bricolage Grotesque em display.
- Paleta: 1 bit mais uma tinta: fundo `oklch(0.94 0.02 100)`, tinta `oklch(0.25 0.03 260)`, spot `oklch(0.65 0.20 35)`.
- Textura: Bayer 8x8 a 1/3 da resolução em fotos e gradientes, halftone a 45 graus.
- Movimento dominante: campo procedural (flow field, autômato, ASCII) que resolve em forma legível; limiar do dither animado como revelação.
- Referência: retratos pontilhados do Config 2026; "coded motion" da Envato. https://elements.envato.com/learn/motion-design-trends

## Como usar as direções

Cada direção é uma ficha completa: grade, tipografia, paleta, textura e movimento dominante. No passo 5 do fluxo, proponha de 2 a 3 fichas diferentes entre si (as daqui ou derivadas do assunto) e mostre um styleframe de cada. Nenhuma pode ser a combinação padrão: condensada gigante à esquerda, quase preto com um acento, mono no canto. `design.py` avisa quando a peça inteira cai nela.
