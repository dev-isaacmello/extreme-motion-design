# Extreme Motion Design

Skill de motion design para agentes de código (Claude, Claude Code, Codex e qualquer agente que leia `SKILL.md`).

O agente escreve o vídeo em código com Remotion e React, mas não enxerga o que renderiza. Por isso a skill impõe um fluxo: o áudio é o relógio, toda cena passa por uma folha de contato que o agente é obrigado a olhar, e o MP4 só é entregue depois de um gate numérico de QA.

## O que ela faz

| Etapa | O que acontece |
|---|---|
| Brief | Objetivo, público, formato, duração, tom e marca em 5 linhas |
| Projeto | Copia o template Remotion com tokens de movimento, câmera 2.5D, tipografia cinética, morph, rig, efeitos e tracking |
| Narração | `tts.py` gera a voz e o tempo real de cada palavra, que passa a ditar os cortes |
| Partitura | `timeline.json` descreve cenas, narração, trilha, SFX e loudness. Vídeo, mixagem e QA leem o mesmo arquivo |
| Trilha e SFX | `music.py` busca faixa com licença verificada ou gera uma localmente. `sfx.py` sintetiza os efeitos |
| Cenas | Construídas com as primitivas do template e a referência da técnica usada |
| Dailies | `contact_sheet.py` monta a grade de frames para revisão visual antes do render final |
| Entrega | `mix.py`, render, `deliver.py` e `qa.py`. Sem FAIL no QA, sai o MP4 com a folha de contato e os créditos |

Técnicas cobertas: keyframing, easing e springs, zoom, pan, whip pan e parallax, motion graphics, tipografia cinética, morphing, loop sem emenda, microinterações de UI, frame a frame, cel animation, stop motion, rigging com IK, lip sync, motion 3D, compositing, motion tracking, match moving e rotoscopia.

## Instalação

### Claude Code (plugin)

```
/plugin marketplace add dev-isaacmello/extreme-motion-design
/plugin install extreme-motion-design@extreme-motion-design
```

A skill fica disponível como `/extreme-motion-design:extreme-motion-design` e também é acionada sozinha quando você pede um vídeo animado.

### Claude Code, Codex, Cursor e outros (skills CLI)

```bash
npx skills add dev-isaacmello/extreme-motion-design
```

Para instalar direto em um agente, no nível do usuário:

```bash
npx skills add dev-isaacmello/extreme-motion-design -g -a claude-code
npx skills add dev-isaacmello/extreme-motion-design -g -a codex
```

### Claude (claude.ai e app desktop)

Gere o zip da pasta da skill e envie em **Customize > Skills**:

```bash
git clone https://github.com/dev-isaacmello/extreme-motion-design
cd extreme-motion-design/skills
zip -r extreme-motion-design.zip extreme-motion-design/
```

O zip precisa ter a pasta `extreme-motion-design/` no topo, com o `SKILL.md` dentro dela.

### Manual

```bash
git clone https://github.com/dev-isaacmello/extreme-motion-design
cp -r extreme-motion-design/skills/extreme-motion-design ~/.claude/skills/     # Claude Code
cp -r extreme-motion-design/skills/extreme-motion-design ~/.agents/skills/     # Codex
```

## Uso

Peça em linguagem natural:

```
crie um vídeo de motion design de 20 segundos, 16:9, com narração suave em pt-BR e trilha calma, apresentando o lançamento do plano anual
```

```
reel 9:16 de 12 segundos com tipografia cinética para esta frase, sem narração, cortando na batida
```

```
anime este logo em 4 segundos com morphing e um loop sem emenda no final
```

## Requisitos

- Node 18 ou mais novo, para o Remotion.
- Python 3.10 ou mais novo. Os scripts declaram as dependências no próprio cabeçalho (PEP 723) e rodam com `uv run`.
- ffmpeg no PATH.

## O que a skill executa e acessa

- `npm install` no projeto do vídeo, que baixa Remotion, React e Three do registro do npm.
- `uv run` nos scripts de `scripts/`, que instala as dependências Python declaradas em cada arquivo (numpy, scipy, librosa, opencv, pillow, soundfile, kokoro-onnx, entre outras).
- `tts.py` baixa o modelo de voz Kokoro do GitHub na primeira execução e guarda em `~/.cache/motion-design/kokoro`.
- `music.py` consulta Incompetech e Openverse para achar trilha com licença `cc0`, `pdm` ou `by`. Com `generate`, a trilha é sintetizada localmente, sem rede.
- Voz premium é opcional e só roda se você pedir: `tts.py --provider elevenlabs`, `openai` ou `azure` envia o roteiro para a API escolhida usando a chave que estiver em `ELEVENLABS_API_KEY`, `OPENAI_API_KEY` ou `AZURE_SPEECH_KEY`. A skill manda o agente perguntar antes de usar API paga.
- Os scripts da skill não acessam nenhum outro endereço.

Os três arquivos `.wav` do template são o áudio do vídeo de exemplo: trilha gerada por `music.py`, narração gerada por `tts.py` com Kokoro e a mixagem das duas. Nenhum tem direitos de terceiros.

## Limites

- O Remotion é gratuito para indivíduos e empresas de até 3 pessoas. Acima disso exige Company License, e a skill avisa quando for o caso.
- O agente revisa frames parados e números de QA. Ritmo e sensação de movimento continuam precisando de um olho humano antes de publicar.
- Renderizar exige Node, ffmpeg e o navegador headless que o Remotion baixa. Em ambientes sem rede ou sem permissão para instalar pacotes, a skill carrega mas o render não roda.
- Tracking, match moving e rotoscopia dependem da qualidade do material filmado. Plano com pouca textura ou muito borrão perde o rastreio.
- As instruções da skill estão em português.

## Licença

MIT
