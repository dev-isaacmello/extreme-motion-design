# Revisor independente

Quem escreveu a cena conhece a intenção e enxerga o que quis fazer, não o que está no frame. A revisão final é de um subagente de contexto limpo, que recebe só a folha de contato e o brief.

## Quando

Depois dos dailies sem FIX seus e antes do render completo. Uma rodada. Segunda rodada só se a primeira devolveu FIX em mais de um terço dos quadros.

## Orçamento de imagens

- Uma folha de contato (`out/sheet.png`), que é uma imagem só.
- No máximo 4 frames em tamanho cheio, só dos quadros que a folha deixou em dúvida (`stills.cjs --times ... --scale 1`).
- Nada de render completo para o revisor. Movimento se julga no `qa.py --timeline` e no draft de meia escala, uma vez.

## Texto do pedido (copie e preencha)

```
Você é revisor de um vídeo de motion design. Você não viu o código nem o roteiro. Leia a imagem
<caminho de out/sheet.png>: é uma folha de contato com início, meio e fim de cada cena, na ordem, com o tempo.

Formato: <16:9 | 9:16 | 1:1>. Público: <uma linha>.

1. Sem ler mais nada, escreva em 3 linhas o que este vídeo diz, para quem e o que ele pede que a pessoa faça.
2. Para cada quadro responda PASS ou FIX com o motivo em uma linha. Procure:
   texto cortado, sobreposto, pequeno demais para celular ou sem contraste;
   quadro vazio ou sem nada legível no começo da cena;
   duas coisas disputando atenção; nada indicando para onde olhar;
   cenas com a mesma composição (mesmo lugar do texto, mesmo cartão, mesma entrada);
   cor fora da paleta, gradiente roxo, brilho genérico, tudo centralizado;
   último quadro que não fecha a ideia.
3. Diga qual é a cena mais fraca e por quê.
Não elogie. Não sugira reescrever o vídeo: aponte o defeito e o quadro.
```

## O que fazer com a resposta

- Compare a resposta 1 com o brief. Se o revisor não recontou a mensagem só pelos frames, o vídeo não funciona mudo: é FIX de roteiro de tela, não de animação.
- Corrija todo FIX ou responda por escrito por que não é defeito. Não rode outro revisor até concordar.
- A entrega diz se houve revisão independente e quantos FIX ela devolveu.
