# Biblioteca de blocos (`src/blocks/`)

Blocos prontos para montar cena. Use um bloco antes de escrever componente novo: eles já seguem a doutrina (entrada por máscara, traço, escala ou posição, cascata de até 500 ms, saída mais curta que a entrada, cor só do tema, tamanhos em `u`). Importe de `../blocks`. A composição `Blocks` (`src/scenes/BlocksDemo.tsx`) mostra todos em sequência: `npx remotion still Blocks out/b.png --frame=46`.

## Preciso de X, use Y

| Preciso de | Use |
|---|---|
| Comparar valores entre categorias | `BarChart` |
| Mostrar evolução no tempo | `LineChart` |
| Mostrar uma parte de um todo ou uma meta | `Donut` |
| Dar peso a um número só | `StatCounter` |
| Mostrar tela de app ou de site | `DeviceFrame` |
| Identificar quem fala | `LowerThird` |
| Legendar a narração | `Captions` |
| Mostrar código ou comando sendo digitado | `CodeWindow` |
| Demonstrar um clique na interface | `Cursor` |
| Apontar um detalhe de uma imagem ou tela | `Callout` |
| Listar benefícios ou tarefas concluídas | `Checklist` |
| Depoimento ou frase de alguém | `QuoteCard` |
| Abrir ou fechar com a marca | `LogoSting` |
| Textura de fundo ou faixa de transição | `Marquee` |
| Explicar um processo em etapas | `Steps` |

## Regras que valem para todos

- **Tempo**: `at` é o frame local em que o bloco começa a entrar (padrão 0). `out` é o frame em que ele já terminou de sair; a saída começa `EXIT` frames antes (12 a 30 fps). Sem `out` o bloco fica até o fim da cena. `ease.exit` concentra o movimento nos últimos frames: para a saída aparecer inteira antes do corte, use `out={len - 2}`.
- **Posição**: blocos de conteúdo (`BarChart`, `LineChart`, `Donut`, `StatCounter`, `DeviceFrame`, `CodeWindow`, `Checklist`, `QuoteCard`, `LogoSting`, `Steps`) têm tamanho próprio e ficam onde a cena os puser: envolva num `div` posicionado dentro de `text` (área segura de `useFormat()`). Blocos de sobreposição (`LowerThird`, `Captions`, `Cursor`, `Callout`, `Marquee`) cobrem o quadro inteiro e se posicionam sozinhos.
- **Tamanho**: `width` e `height` são px reais (calcule com `text.w`, `u` ou `pick`). `size` e `fontSize` são px do quadro de 1080 e o bloco multiplica por `u`.
- **Cor**: tudo vem de `C` em `theme.ts`. As props `color` e `accent` aceitam outra cor do tema; não passe hex solto.
- **Dados**: os exemplos abaixo usam rótulos neutros. Na cena, só dado do usuário ou com fonte.
- **Uma ação por vez**: ponha um bloco herói por cena. Dois blocos entrando juntos pedem `at` defasado de 4 a 8 frames.
- Utilitários exportados para cena que precise do mesmo comportamento: `useBlock(at, out)`, `Rise` (subida por máscara), `trim(p)` (trim path), `surface(p, u)`, `mix`, `alpha`, `wrap`, `EXIT`.

## BarChart

Barras que crescem da linha de base em cascata, com rótulo embaixo e valor contando em cima.
Quando usar: comparar de 3 a 7 categorias, com uma delas em destaque.

| Prop | Tipo | Padrão |
|---|---|---|
| `data` | `{label: string; value: number}[]` | obrigatório |
| `highlight` | `number` (índice) | a barra de maior valor |
| `width`, `height` | `number` | `text.w` e o menor entre `text.h` e 56% da largura |
| `max` | `number` | maior valor |
| `format` | `(v: number) => string` | `toLocaleString('pt-BR')` |
| `color`, `accent` | `string` | neutro do tema e `C.accent` |
| `at`, `out` | `number` | `0` e sem saída |

```tsx
<BarChart
	at={6}
	out={len - 2}
	width={text.w * 0.74}
	data={[{label: 'Série A', value: 24}, {label: 'Série B', value: 38}, {label: 'Série C', value: 52}]}
/>
```

## LineChart

Linha que se desenha por trim path, com um ponto viajando na ponta e o valor final ao chegar; grade discreta de quatro linhas.
Quando usar: tendência ao longo do tempo, de 4 a 12 pontos. A escala parte de zero, a não ser que você passe `min`.

| Prop | Tipo | Padrão |
|---|---|---|
| `points` | `number[]` | obrigatório |
| `labels` | `string[]` (eixo x, de ponta a ponta) | sem rótulos |
| `width`, `height` | `number` | como no `BarChart` |
| `min`, `max` | `number` | `0` (ou o menor valor, se negativo) e o maior valor |
| `format` | `(v: number) => string` | `toLocaleString('pt-BR')` |
| `color` | `string` | `C.accent` |
| `area` | `boolean` | `true` |
| `at`, `out` | `number` | `0` e sem saída |

```tsx
<LineChart at={6} out={len - 2} points={[12, 18, 15, 27, 24, 36, 48]} labels={['Início', 'Fim']} />
```

## Donut

Anel de progresso com o número contando no centro.
Quando usar: percentual ou meta única. Para comparar várias fatias, use `BarChart`.

| Prop | Tipo | Padrão |
|---|---|---|
| `value` | `number` | obrigatório |
| `max` | `number` | `100` |
| `suffix` | `string` | `'%'` |
| `label` | `string` | sem rótulo |
| `size` | `number` (diâmetro, vezes `u`) | `440` |
| `thickness` | `number` (vezes `u`) | 8,5% do diâmetro |
| `color` | `string` | `C.accent` |
| `at`, `out` | `number` | `0` e sem saída |

```tsx
<Donut value={72} label="Meta de exemplo" at={6} out={len - 2} />
```

## StatCounter

Número herói que conta com `ticker` e `tabular-nums`, com prefixo, sufixo e rótulo. A largura do valor final fica reservada, então nada treme enquanto conta.
Quando usar: o dado principal da cena. Deixe o valor parado por 1 s ou mais depois de chegar.

| Prop | Tipo | Padrão |
|---|---|---|
| `value` | `number` | obrigatório |
| `from` | `number` | `0` |
| `prefix`, `suffix` | `string` | nenhum |
| `label` | `string` | nenhum |
| `decimals` | `number` | `0` |
| `size` | `number` (altura do número, vezes `u`) | `240` |
| `align` | `'left' \| 'center' \| 'right'` | `'left'` |
| `count` | `number` (frames da contagem a 30 fps) | `34` |
| `color`, `accent` | `string` | `C.ink` e `C.accent` (sufixo) |
| `at`, `out` | `number` | `0` e sem saída |

```tsx
<StatCounter value={1280} suffix="+" label="Valor de demonstração" at={6} out={len - 2} />
```

## DeviceFrame

Moldura de celular ou de janela de browser; os filhos são a tela.
Quando usar: demo de produto, gravação de tela ou UI recriada em React. Os filhos ocupam a tela com `position: absolute; inset: 0` e animam por conta própria.

| Prop | Tipo | Padrão |
|---|---|---|
| `variant` | `'phone' \| 'browser'` | `'phone'` |
| `children` | `ReactNode` | tela vazia |
| `width` | `number` | o que cabe na área segura |
| `url` | `string` (só browser) | `'exemplo.com.br'` |
| `ratio` | `number` (altura da tela do browser sobre a largura) | `0.6` |
| `screen` | `string` (cor de fundo da tela) | neutro do tema |
| `at`, `out` | `number` | `0` e sem saída |

```tsx
<DeviceFrame variant="browser" width={text.w * 0.62} url="exemplo.com.br" at={6} out={len - 2}>
	<MinhaTela />
</DeviceFrame>
```

O celular tem proporção 1 por 2,08. A ilha no topo ocupa uma faixa de 12% da largura do aparelho: deixe esse espaço livre no conteúdo.

## LowerThird

Nome e cargo no canto de baixo da área segura: a barra de acento cresce e as duas linhas sobem por máscara.
Quando usar: identificar quem fala em vídeo gravado ou em depoimento. Sobre imagem clara, ligue `plate`.

| Prop | Tipo | Padrão |
|---|---|---|
| `name` | `string` | obrigatório |
| `role` | `string` | nenhum |
| `side` | `'left' \| 'right'` | `'left'` |
| `plate` | `boolean` | `false` |
| `accent` | `string` | `C.accent` |
| `at`, `out` | `number` | `0` e sem saída |

```tsx
<LowerThird name="Nome Sobrenome" role="Cargo de exemplo" at={12} out={102} />
```

Tempo de leitura: 1,5 s mais 0,3 s por palavra entre `at` e `out`.

## Captions

Legenda por página, com até 2 linhas dentro da área segura de texto e a palavra falada no acento.
Quando usar: toda narração em vídeo vertical e sempre que o vídeo precisa funcionar sem som. Para tipografia cinética grande, use `KineticWords`.

| Prop | Tipo | Padrão |
|---|---|---|
| `words` | `{word: string; start: number; end: number}[]` em segundos absolutos | obrigatório |
| `offsetSec` | `number` | `0` |
| `maxChars` | `number` (teto por linha) | `36` |
| `fontSize` | `number` (vezes `u`) | `56` |
| `position` | `'bottom' \| 'center' \| 'top'` | `'bottom'` |
| `color`, `accent` | `string` | `C.ink` e `C.accent` |
| `plate` | `string` (cor da tarja atrás de cada linha; use sobre vídeo filmado) | sem tarja |

```tsx
<Captions words={WORDS} />                       // WORDS de lib/score já está em tempo absoluto
<Captions words={WORDS} plate={C.bg} />         // sobre filmagem
```

- A página fecha em fim de frase, em pausa acima de 0,6 s ou quando enche; página cheia fecha na última vírgula.
- O número de caracteres por linha cai sozinho quando a largura segura é pequena (9:16), então a linha nunca passa de 80% do quadro.
- Monte no nível raiz, como o `KineticWords`. Dentro de um `<Sequence from>`, `offsetSec` é o início da narração menos o início da sequência, em segundos.
- Não tem `at` nem `out`: quem manda é o tempo das palavras.

## CodeWindow

Janela de código ou de terminal com digitação por caractere derivada do frame, cursor que pisca por frame e realce simples.
Quando usar: mostrar um comando, um trecho de API ou uma instalação. Até 6 linhas de 40 caracteres; a fonte encolhe para a linha mais longa caber.

| Prop | Tipo | Padrão |
|---|---|---|
| `code` | `string` (linhas separadas por `\n`) | obrigatório |
| `variant` | `'code' \| 'terminal'` | `'code'` |
| `title` | `string` | `'exemplo.ts'` ou `'terminal'` |
| `cps` | `number` (caracteres por segundo) | `32` |
| `prompt` | `string` (só terminal) | `'$ '` |
| `width` | `number` | o menor entre `text.w` e `1100 * u` |
| `fontSize` | `number` (vezes `u`) | `30` |
| `at`, `out` | `number` | `0` e sem saída |

```tsx
<CodeWindow
	variant="terminal"
	code={'$ npm install\npacotes instalados\n$ npm run render'}
	at={6}
	out={len - 2}
/>
```

- No terminal, só a linha que começa com `prompt` é digitada; as outras são saída e entram inteiras.
- A digitação começa 12 frames depois de `at` e cada linha digitada custa `caracteres / cps` segundos mais 5 frames. Some as linhas antes de fechar a duração da cena.
- Realce: palavra-chave no acento, string e número em `C.second`, comentário em `C.muted`. Não é um parser: serve para trechos curtos.

## Cursor

Cursor de demo que viaja em arco entre pontos, pausa, clica com escala e ripple.
Quando usar: mostrar interação em UI recriada ou em tela dentro de `DeviceFrame`.

| Prop | Tipo | Padrão |
|---|---|---|
| `path` | `{x: number; y: number; at: number; click?: boolean}[]` | obrigatório |
| `size` | `number` (altura da seta, vezes `u`) | `52` |
| `color` | `string` | `C.ink` |
| `out` | `number` | sem saída |

```tsx
<Cursor
	out={len - 2}
	path={[
		{x: width * 0.8, y: height * 0.8, at: 12},
		{x: botao.x, y: botao.y, at: 40, click: true},
	]}
/>
```

- `x` e `y` são px do quadro. `at` é o frame do evento: a chegada ou, com `click`, o clique (o cursor chega `CLICK_PAUSE` = 5 frames antes e espera).
- O primeiro ponto é onde o cursor aparece. A viagem dura de 10 a 26 frames conforme a distância; dê pelo menos esse intervalo entre dois `at`.
- A interface responde 1 frame depois do clique: `pop(frame, fps, clickAt + 1, springs.snappy)`. O SFX `click` vai no mesmo frame do `at`.

## Callout

Rótulo com linha guia: um ponto marca o alvo, a linha se desenha até o cotovelo e segue por baixo do texto.
Quando usar: nomear uma parte de uma imagem, de um gráfico ou de uma tela. No máximo dois por cena, com `at` defasado.

| Prop | Tipo | Padrão |
|---|---|---|
| `from` | `{x: number; y: number}` (alvo, px do quadro) | obrigatório |
| `to` | `{x: number; y: number}` (cotovelo, px do quadro) | obrigatório |
| `label` | `string` | obrigatório |
| `detail` | `string` | nenhum |
| `width` | `number` (trecho horizontal) | `380 * u` |
| `color`, `accent` | `string` | `C.ink` e `C.accent` |
| `at`, `out` | `number` | `0` e sem saída |

```tsx
<Callout from={{x: 620, y: 480}} to={{x: 760, y: 340}} label="Ponto de interesse" detail="Detalhe em uma linha" at={14} out={len - 2} />
```

O texto abre para o lado oposto ao alvo: com `to.x` menor que `from.x` ele alinha à direita. Confira se `to.x` mais `width` fica dentro de `text`.

## Checklist

Itens em cascata; depois que todos chegam, o check de cada um se desenha por traço, um a um.
Quando usar: benefícios, requisitos, o que está incluso. De 3 a 5 itens de até 30 caracteres.

| Prop | Tipo | Padrão |
|---|---|---|
| `items` | `string[]` | obrigatório |
| `done` | `number` (quantos ganham check, do primeiro em diante) | todos |
| `width` | `number` | o menor entre `text.w` e `900 * u` |
| `fontSize` | `number` (vezes `u`) | `44` |
| `accent` | `string` | `C.accent` |
| `at`, `out` | `number` | `0` e sem saída |

```tsx
<Checklist items={['Primeiro item', 'Segundo item', 'Terceiro item']} at={6} out={len - 2} />
```

## QuoteCard

Citação tipográfica: aspas no acento, texto revelado linha a linha e, por último, traço e autor.
Quando usar: depoimento ou frase de impacto. Só com frase e autor fornecidos pelo usuário.

| Prop | Tipo | Padrão |
|---|---|---|
| `quote` | `string \| string[]` (texto corrido ou linhas prontas) | obrigatório |
| `author`, `role` | `string` | nenhum |
| `width` | `number` | `text.w` |
| `maxChars` | `number` (por linha) | `30`, ou `22` em 9:16 |
| `fontSize` | `number` (vezes `u`) | `64` |
| `accent` | `string` | `C.accent` |
| `at`, `out` | `number` | `0` e sem saída |

```tsx
<QuoteCard
	quote="Uma frase de exemplo ocupa este espaço em duas ou três linhas."
	author="Nome da pessoa"
	role="Cargo de exemplo"
	width={text.w * 0.72}
	at={6}
/>
```

A fonte encolhe para a linha mais longa caber em `width`. Até 4 linhas; mais que isso não dá tempo de ler.

## LogoSting

Assinatura de marca em quatro fases dentro de `length`: construção (uma linha no acento se desenha, 45%), resolução (a marca sobe de trás da linha, que recolhe para um sublinhado), hold e assinatura (o `tagline` entra em 80%).
Quando usar: fecho do vídeo. Nunca na abertura.

| Prop | Tipo | Padrão |
|---|---|---|
| `text` | `string` | nenhum |
| `children` | `ReactNode` (logo em SVG ou `Img`, no lugar de `text`) | nenhum |
| `tagline` | `string` | nenhum |
| `length` | `number` (frames das quatro fases) | `72` |
| `size` | `number` (vezes `u`) | `148` |
| `color`, `accent` | `string` | `C.ink` e `C.accent` |
| `at`, `out` | `number` | `0` e sem saída |

```tsx
<LogoSting text="Marca" tagline="Assinatura da marca" length={72} at={6} />
```

O impacto do áudio cai no frame `at + length * 0.45`. Segure o quadro final por 1 s ou mais. Para o logo real, passe o arquivo como filho; não redesenhe marca que o usuário não forneceu.

## Marquee

Faixa de texto em loop sem emenda, para fundo ou transição.
Quando usar: textura atrás de um herói (`outline`), faixa que cruza o quadro numa troca de cena (`band`). É ornamento: não carrega informação que precise ser lida.

| Prop | Tipo | Padrão |
|---|---|---|
| `items` | `string[]` | obrigatório |
| `variant` | `'outline' \| 'solid' \| 'band'` | `'outline'` |
| `period` | `number` (frames para andar uma repetição do texto) | `150` |
| `direction` | `1 \| -1` | `1` (para a esquerda) |
| `y` | `number` (centro, px a partir do topo) | meio do quadro |
| `rotate` | `number` (graus) | `0` |
| `fontSize` | `number` (vezes `u`) | `148` |
| `fill` | `string` (dentro das letras no `outline`) | `C.bg` |
| `color`, `accent` | `string` | conforme a variante e `C.accent` |
| `at`, `out` | `number` | `0` e sem saída |

```tsx
<Marquee items={['Texto em loop', 'Sem emenda']} period={90} y={height * 0.44} at={6} out={len - 2} />
<Marquee items={['Faixa de transição']} variant="band" direction={-1} rotate={-3} fontSize={72} y={height * 0.62} />
```

- O frame `at + period` é idêntico ao `at`: para vídeo em loop, use um período que divida a duração.
- No `outline` as letras são preenchidas com `fill`, que precisa ser a cor do fundo atrás da faixa.
- A faixa sangra do quadro e leva `data-decor`, então a sonda de layout não a mede.

## Steps

Linha do tempo de 3 a 5 passos: o trilho se desenha, os nós entram em cascata e o acento avança até o passo ativo.
Quando usar: explicar processo ou mostrar em que etapa a história está. Em linha em 16:9 e 1:1, em coluna em 9:16.

| Prop | Tipo | Padrão |
|---|---|---|
| `steps` | `{title: string; detail?: string}[]` | obrigatório |
| `active` | `number` (índice, 0 é o primeiro) | `0` |
| `direction` | `'row' \| 'column'` | pelo formato |
| `width` | `number` | `text.w` |
| `accent` | `string` | `C.accent` |
| `at`, `out` | `number` | `0` e sem saída |

```tsx
<Steps
	active={1}
	at={6}
	steps={[{title: 'Briefing', detail: 'Objetivo e formato'}, {title: 'Roteiro'}, {title: 'Entrega'}]}
/>
```

Em linha, título de até 12 caracteres com 5 passos. Para avançar o passo ao longo do vídeo, monte um `Steps` por cena com `active` diferente.

## Limites conhecidos

- Os blocos estimam largura de texto por contagem de caracteres (`Captions`, `QuoteCard`, `CodeWindow`, `Marquee`), calibrada para Inter e JetBrains Mono. Se trocar a fonte em `theme.ts`, renderize um still de cada bloco usado e confira.
- `Cursor` e `Callout` recebem px do quadro: recalcule os pontos por formato com `useFormat()`.
- Nenhum bloco toca áudio. SFX e narração continuam na partitura.
