# Modo referência: fazer uma peça nova com a estrutura de um vídeo que o usuário mostrou

Quando o usuário entrega um vídeo e diz "quero algo assim", o gosto deixa de ser o do modelo. A referência vira medida: o script desmonta o vídeo em números, o agente olha a folha, a peça nova é construída sobre os mesmos tempos e, no fim, outra medida diz o quanto ficou parecida.

## Fluxo

```bash
uv run <skill>/scripts/reference.py analyze referencia.mp4 -o reference
uv run <skill>/scripts/reference.py plan reference/reference.json -o roteiro.json
# ... direção, cenas, lint, dailies, render ...
uv run <skill>/scripts/reference.py compare reference/reference.json out/final.mp4 --timeline public/timeline.json --min 70
```

1. **Analise.** `analyze` escreve `reference/reference.json`, três keyframes por plano e `reference/sheet.png`.
2. **Olhe a folha.** Número não diz que fonte é, se o texto está em caixa alta, se há grão, o que cada plano mostra. Escreva em `direction.json` o que você viu: família tipográfica (serifada, grotesca, condensada, mono), tratamento (chapado, foto, 3D, textura), tipo de transição e o papel de cada plano na história.
3. **Planeje.** `plan` escreve um `roteiro.json` com uma cena por plano, na duração da referência. Planos mais curtos que 0,7 s viram uma cena de montagem. Troque os ids por nomes, ponha a fala, as marcas e os SFX, e rode o `score.py`. Se a peça nova tem narração, a fala precisa caber nos tempos: corte texto, não estique a referência.
4. **Construa** cada cena com o movimento de câmera, a energia e o lugar da massa visual que o plano correspondente tem (`camera`, `energy`, `mass` em cada cena do roteiro).
5. **Meça.** `compare` dá a nota de fidelidade e a parcela de cada eixo. Corrija o eixo mais baixo primeiro.

## O que é medido

| Campo | O que é | Como é obtido |
|---|---|---|
| `shots` | planos, com início, fim e duração | corte seco por salto de histograma HSV, com limiar adaptado ao próprio vídeo |
| `energy`, `peak_at` | quanto o plano se mexe e onde está o pico | diferença média entre frames, relativa ao percentil 90 do vídeo |
| `camera` | zoom in, zoom out, pan, tilt ou parado | cantos seguidos por Lucas-Kanade e transformação afim parcial acumulada |
| `palette`, `bg`, `accent` | cores do plano e quanto cada uma ocupa | k-means em Lab sobre três frames |
| `layout` | onde está a massa visual | energia de borda numa grade 3x3 e o centro de massa |
| `audio` | BPM, batidas, loudness, fração de cortes na batida | librosa e `ebur128` |

## A nota de fidelidade

| Eixo | Peso | Como compara |
|---|---|---|
| ritmo | 0,30 | posição dos cortes, no tempo normalizado, com tolerância de um quarto do plano médio |
| energia | 0,25 | correlação entre as curvas de movimento |
| composição | 0,15 | correlação das grades 3x3, plano a plano |
| cor | 0,15 | distância em Lab de cada cor da referência à mais próxima do vídeo novo, pesada pela área |
| câmera | 0,10 | mesmo tipo de movimento em cada plano |
| duração | 0,05 | diferença relativa |

- `--timeline` usa as fronteiras de cena da partitura como cortes. Use sempre em motion graphics, onde a troca de cena costuma ser uma transição e não um corte seco.
- `--skip cor` tira a paleta da nota quando a marca do usuário manda nas cores. Vale para qualquer eixo.
- `--min 70` faz o script sair com erro abaixo da nota.

Calibração feita na produção da 2.0.0, com um reel de 28,7 s e 14 planos como referência: ele contra ele mesmo dá 100; com `--timeline` (7 cenas no lugar de 14 cortes) dá 86; um reel feito a partir do mesmo pedido, mas sem a referência, dá 38; dois vídeos sem relação dão 23 e 24. Abaixo de 40 a peça não seguiu a referência; acima de 70 seguiu.

## O que pode e o que não pode ser reproduzido

Reproduza a ideia: estrutura, duração e ritmo dos planos, tipo de movimento, lógica da composição, relação entre som e corte, família de técnica. Não reproduza a expressão: nenhum frame, asset, logo, personagem, ilustração, fonte licenciada, texto ou trilha da referência entra na peça nova, e a peça não pode ser confundida com a marca do outro. Se o pedido for uma cópia quadro a quadro de um vídeo de terceiro, pare e diga isso ao usuário.

A referência entra como arquivo que o usuário entrega. A skill não baixa vídeo de plataforma.

## Limites

- A nota mede estrutura, não qualidade nem conteúdo. Uma peça ruim pode ter nota alta.
- Corte seco é detectado; fusão, wipe e morph longos não viram corte. Em referência de motion graphics sem corte seco, confira a contagem de planos na folha.
- O BPM vem da faixa mixada. Com voz por cima ele erra, inclusive pela metade ou pelo dobro: no reel de calibração a faixa tem 128 BPM e a medida deu 86. Trate `bpm` e `cuts_on_beat` como pista.
- Movimento de câmera é estimado pelo fundo. Em plano dominado por um objeto que se move, o objeto pode ser lido como câmera.
- Tipografia, textura e significado não são medidos: é o que a folha existe para mostrar.
