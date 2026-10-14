# Imagem e vídeo reais: acervo livre, sem crédito obrigatório

Motion design sobre o mundo real pede material real. `scripts/stock.py` busca foto e vídeo em acervos de licença livre, confere a licença de cada arquivo na resposta da API e registra a evidência em `credits.json`. O tratamento da imagem (duotone, recorte, parallax, Ken Burns, texto preso à cena, grade) está em `design.md`, seção 6.

```bash
uv run <skill>/scripts/stock.py commons --q "clouds timelapse" --type video --list
uv run <skill>/scripts/stock.py commons --q "clouds timelapse" --type video --pick 3 -o public/stock/nuvens.mp4
uv run <skill>/scripts/stock.py nasa --q "earth from orbit" --type video -o public/stock/terra.mp4
uv run <skill>/scripts/stock.py openverse --q "mountain lake" --orientation tall -o public/stock/lago.jpg
uv run <skill>/scripts/stock.py met --q "sunflowers" -o public/stock/girassois.jpg
```

Sempre liste primeiro (`--list`), escolha pelo título, tamanho e dimensão, baixe e OLHE o arquivo antes de usar.

## Fontes

| Fonte | Tem | Chave | O que o script aceita | Crédito | Limite |
|---|---|---|---|---|---|
| `commons` (Wikimedia Commons) | foto e vídeo | não | só arquivo com `License` cc0 ou pd, `AttributionRequired` false e sem `Restrictions` | não exigido | busca literal, muita filmagem documental e de governo; vídeo em webm ou ogv, convertido para h264; a página avisa que não dá garantia do status |
| `nasa` (NASA Image and Video Library) | foto e vídeo | não | tudo do acervo | a NASA pede, não exige | tema espacial e científico; logotipo e insígnia da NASA não são livres; astronauta e funcionário atual não podem aparecer em promoção comercial; não sugerir endosso |
| `openverse` | só foto | não | `license=cc0,pdm` | não exigido | a licença é declarada por quem publicou e o Openverse não verifica; 20 requisições por minuto e 200 por dia sem cadastro |
| `met` (The Met Open Access) | foto de obra | não | só objeto com `isPublicDomain` verdadeiro | não exigido | só obra de arte; duas chamadas por imagem |
| `pixabay` | foto e vídeo | gratuita, `PIXABAY_API_KEY` no `.env` | tudo (Pixabay Content License) | não exigido | proíbe download em massa e redistribuição do arquivo solto; sem garantia sobre pessoas e marcas |

Fontes que ficaram de fora, com o motivo conferido em 2026-10-13: Pexels (a página da API diz que a emissão de chave nova está pausada), Unsplash (as regras da API exigem hotlink e atribuição), Mixkit (os termos proíbem script), Coverr (exige chave e a URL expira em 15 minutos), Videvo (redireciona para o Freepik), Prelinger no Internet Archive (só parte é domínio público e a própria FAQ avisa).

## O que a licença livre não cobre

CC0 e domínio público resolvem o direito autoral e mais nada. Continuam exigindo autorização:

- **Pessoa reconhecível.** Nenhuma dessas fontes entrega autorização de imagem. Em peça comercial, não use rosto reconhecível.
- **Marca e logotipo** visíveis no quadro.
- **Obra de arte recente, arquitetura protegida, tela de produto** ao fundo.

O script não detecta nada disso. Olhe o arquivo, e na dúvida escolha outro. Diga na entrega de onde veio cada imagem; o `credits.json` tem a fonte, a URL, a licença e os campos lidos na API, mesmo quando o crédito não é obrigatório.

## Limites

- A marcação de licença vem do acervo. O script confere o que a API declara, não o que é verdade.
- O áudio de vídeo baixado é removido na conversão: a trilha embutida pode ter outro dono.
- Material de governo dos EUA domina o Commons em vídeo. Para tema brasileiro ou urbano a busca rende pouco.
- `pixabay` foi escrito a partir da documentação oficial e não foi executado: não havia chave nesta máquina.
