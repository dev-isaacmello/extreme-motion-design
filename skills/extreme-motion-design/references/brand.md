# Marca: extrair uma vez, reusar em todo vídeo

`scripts/brand.py` lê a marca real de um site, de um repositório ou de imagens e escreve `brand.json` (formato de `public/brand.json` do template), `BRAND.md` (para ler antes de escrever roteiro e cenas) e `assets/` (logo, ícones, og:image, screenshots).

## Quando rodar

- No brief, antes de qualquer cena, sempre que o vídeo é de uma marca que já existe (site no ar, produto com código, ou só telas).
- Uma vez por marca. Se já existe uma pasta `brand/` ao lado dos projetos de vídeo, use a que está lá e não rode de novo. Rode de novo só quando a marca mudou.
- Não rode para peça sem marca: o `brand.json` do template já serve.

## Os três modos

```bash
uv run <skill>/scripts/brand.py --url https://exemplo.com -o brand/           # site no ar
uv run <skill>/scripts/brand.py --repo ../meu-app/apps/web -o brand/          # código local, somente leitura
uv run <skill>/scripts/brand.py --screens telas/ -o brand/                    # só imagens
uv run <skill>/scripts/brand.py --url https://exemplo.com --repo ../meu-app/apps/web -o brand/   # somam evidência
```

- `--url`: baixa o HTML e as folhas de estilo (linkadas e `@import`), tira screenshot 1440x900 e 390x844 e confere a paleta do CSS contra os pixels. É o modo mais confiável, porque `bg` e `ink` saem do que aparece na tela.
- `--repo`: lê CSS com custom properties, `tailwind.config.*`, objetos de tema em TS/JS, `package.json`, `next/font`, `@font-face`, Google Fonts e logos em `public/`, `static/` e `assets/`. Não executa nem instala nada. Aponte para a pasta do front-end (a que tem `package.json` e `globals.css`), não para a raiz do monorepo. Pode repetir `--repo`. Um `@import "@escopo/pacote/tokens.css"` de pacote do mesmo workspace é seguido, o que lê arquivos fora da pasta informada.
- `--screens`: só pixels. Entrega `bg`, `ink` e `accent`; `muted`, `line`, `second`, fontes, nome e logo ficam `null`.
- Rode a partir da pasta do projeto de vídeo (a que tem `node_modules`): é ali que o script procura o Chrome do Remotion e confere se a fonte existe em `@remotion/google-fonts`.
- `-o` não pode ficar dentro do repositório analisado.

## Ler o resultado antes de usar

- `missing` lista o que não foi achado. Esses campos estão `null`. Não preencha por conta própria: mostre a lista ao usuário e pergunte (é um dos casos de "parar e perguntar" do SKILL.md).
- `warnings` traz contraste abaixo do mínimo (ink/bg 4,5 e accent/bg 3) com o número medido, accent que não aparece na tela, fonte que não existe no Google Fonts e falhas de rede ou de screenshot. A cor da marca nunca é alterada para passar no contraste: com aviso de accent/bg, use o accent em área grande ou sobre outra superfície.
- `evidence` diz de onde saiu cada valor, os temas claro e escuro encontrados e qual foi escolhido, e as candidatas a acento com pontuação. Abra `assets/screenshot-desktop.png` e compare com a paleta antes de aceitar.
- `BRAND.md` traz título, descrição e as primeiras chamadas da página citadas como estão. Use como referência de tom, não como texto do vídeo.

## Levar para o vídeo

1. Resolva com o usuário todo campo `null` de `colors` e `fonts`. O template lê `brand.colors` direto: `null` quebra a cena.
2. Copie `brand/brand.json` para `public/brand.json` do projeto do vídeo e `brand/assets/logo.*` para `public/assets/` (o campo `logo` é um caminho relativo a `public/`; na cena, carregue com `staticFile(BRAND.logo)`).
3. Fonte: se `evidence.fonts_google` marca a família como existente, troque o import em `src/theme.ts` por `@remotion/google-fonts/<NomeSemEspaços>` (Bricolage Grotesque vira `BricolageGrotesque`). Se não existe, a fonte é proprietária: carregue o arquivo com `@remotion/fonts` quando o usuário tiver a licença e o arquivo, ou escolha a substituta com ele. O script não baixa arquivo de fonte.
4. Rode `lint.py`: cor fora de `C.*` continua sendo aviso.

## Onde guardar

Uma pasta `brand/` ao lado dos projetos de vídeo, versionada com eles:

```
videos/
  brand/            brand.json, BRAND.md, assets/
  lancamento-v2/    public/brand.json copiado de ../brand
  tutorial-caixa/
```

Com mais de uma marca, uma subpasta por marca (`brand/arena7/`, `brand/voxy/`).

## Limites reais

- **Acento é heurística.** A escolha soma nome de variável (primary, brand, accent, cta, acento, marca, acao), uso em seletores de botão, link e destaque, uso de classes utilitárias no código e presença nos pixels. Em marca monocromática, ou quando o site tem várias cores fortes, pode sair `null` ou a cor errada. Confira sempre contra o screenshot e as candidatas em `evidence`.
- **`second` quase sempre sai `null`.** Só entra com variável de nome explícito (secondary, accent-2) ou uso forte e visível. Em 8 alvos testados saiu em 1.
- **Só a primeira tela.** O screenshot é a dobra inicial, com 8 s de tempo virtual. Banner de cookie, animação de entrada e hero com foto ou vídeo entram na conta dos pixels. O que está abaixo da dobra não é visto.
- **Só pixels não separa marca de ilustração.** No modo `--screens` o accent é a cor saturada mais frequente: se a tela tem foto, é a foto.
- **CSS montado por JavaScript não é lido.** Site que injeta estilo em tempo de execução (CSS-in-JS sem SSR) cai no modo só pixels. Site que responde 403 a robô não entrega nada: o script registra o erro e não insiste. Não lê `robots.txt`.
- **Tema.** Reconhece `.dark`, `.light`, `[data-*="dark"]`, `prefers-color-scheme` e os nomes `claro` e `escuro`. Tema com outro nome de classe não é reconhecido e os valores se misturam com o padrão. Sem screenshot, o tema padrão sai das dicas do HTML ou do escopo sem tema.
- **Cores.** Normaliza hex, `rgb()`, `hsl()`, `oklch()`, `oklab()`, `color(srgb|display-p3)`, nomes CSS, `var()` encadeado e `color-mix()` em srgb e oklab. Não resolve `calc()`, cor relativa (`from`), `lab()`, `lch()` nem `color-mix()` em outros espaços. Cor fora do sRGB é cortada canal a canal e vira aviso. Cor com alfa em `muted` e `line` é composta sobre `bg`.
- **Tailwind.** Só resolve cor que o projeto define (custom property, `@theme`, `colors` do config). Classe da paleta padrão (`bg-zinc-950`) no JSX não é resolvida. `tailwind.config` e tema em TS só quando o objeto é literal: valor calculado, importado ou gerado por função é ignorado.
- **Fontes.** Só o nome. `next/font/local` tem o nome deduzido do arquivo. Pilha de fontes do sistema vira `null` com aviso. A checagem em `@remotion/google-fonts` só acontece quando o pacote está instalado a partir da pasta atual.
- **Logo.** No site: `<img>` ou SVG inline no cabeçalho, JSON-LD. SVG com `currentColor` é salvo como está e renderiza preto fora do site. Logo em sprite (`<use>`) não é capturado. No repositório: arquivos com logo, brand ou marca no nome; logo escrito como componente JSX não é achado. O script copia um e lista os outros em `evidence.logo_alternatives`.
- **Tom.** Só título, descrição e `h1`/`h2`. No repositório, só texto literal em página inicial e componentes de landing; título montado com variável ou componente fica de fora.
- **Chrome.** Tenta com sandbox cada binário, na ordem `node_modules/.remotion`, `chromium`, `chromium-browser`, `google-chrome`. No Ubuntu 24.04 o `chrome-headless-shell` do Remotion não inicia com sandbox (restrição de user namespace do AppArmor) e o script segue para o próximo. `--allow-no-sandbox` libera a segunda rodada sem sandbox e deixa aviso; esse caminho não foi verificado. A página é aberta com o user agent do próprio Chrome.
- **Rede.** Até 140 requisições, 90 folhas de estilo e 4 MB por arquivo, sem nova tentativa. Site com mais CSS que isso é lido em parte.
