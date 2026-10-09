# Voz: a pergunta obrigatória, os três caminhos e os tempos por palavra

## A pergunta (sempre, antes do roteiro)

Rode `python3 <skill>/scripts/voice.py`. Ele mede a máquina e imprime a pergunta com as três opções já preenchidas. Faça a pergunta ao usuário com a ferramenta de pergunta do agente (AskUserQuestion no Claude Code) ou em texto, e espere a resposta. Não escolha por ele. Só dispense a pergunta quando o pedido já respondeu com todas as letras ("sem narração", "com a minha chave da ElevenLabs"); nesse caso confirme em uma linha.

| Opção | O que muda no fluxo |
|---|---|
| Sem voz | Não há `tts.py`. A tipografia vira a narração: leia "Funcionar sem som" em `references/direction.md`. As cenas saem das batidas da trilha (`beats.py`) ou do texto de tela |
| Voz com ElevenLabs | Voz de estúdio por API paga. Siga "ElevenLabs" abaixo |
| Voz local | Modelo aberto rodando na máquina do usuário, escolhido pelo hardware. Siga "Voz local" abaixo |

Junto com a opção de voz local, ofereça ouvir antes de decidir: `voice.py --audition "<primeira frase do roteiro>" -o out/vozes` gera a mesma frase em cada voz do Kokoro.

## ElevenLabs

1. **Chave**: o usuário cria em https://elevenlabs.io/app/settings/api-keys. A chave nasce restrita: precisa de Text to Speech (Access) e Voices (Read). Esses nomes vêm da central de ajuda; se a tela mostrar outros, vale a permissão de gerar fala e a de ler vozes.
2. **Onde guardar**: o próprio usuário grava `ELEVENLABS_API_KEY=...` num arquivo `.env` na pasta do vídeo (o `.gitignore` do template ignora `.env`; o `lint.py` reprova o projeto que tem `.env` sem essa regra). `tts.py` e `voice.py` leem esse arquivo. Nunca peça para colar a chave no chat e nunca a escreva em arquivo versionado, comando ou log.
3. **Validar sem gastar**: `python3 <skill>/scripts/voice.py --check-key` lista as vozes da conta. HTTP 401 é chave errada; 403 é permissão faltando.
4. **Voz**: escolha com o usuário uma voz da lista devolvida, de sotaque brasileiro. O sotaque vem da voz, não de parâmetro. Não use as vozes Default: expiram em 31/12/2026 segundo a documentação.
5. **Custo**: antes de gerar, diga quantos caracteres o roteiro tem e peça o sim. O plano Free dá 10 mil créditos por mês e não inclui licença comercial; vídeo para cliente pede plano pago.
6. **Gerar**: `uv run <skill>/scripts/tts.py roteiro.txt -o public/audio/narration --provider elevenlabs --voice <voice_id>`.

Modelos (conferidos em 2026-10-09): o padrão do script é `eleven_multilingual_v2`, estável em texto longo e com tempos reais por caractere no endpoint `with-timestamps`. `eleven_v4` é o modelo principal atual e lista português do Brasil, mas o suporte a `with-timestamps` nele não foi confirmado: se usar `--model eleven_v4` e os tempos não vierem, gere o áudio e rode `align.py`. `eleven_turbo_v2_5` está descontinuado.

## Voz local

`voice.py` decide com memória **livre**, não nominal: VRAM livre da GPU, RAM disponível, threads e disco. Ele imprime o recomendado, a alternativa e por que cada outro modelo foi descartado nesta máquina. A tabela de modelos vive em `assets/tts-models.json` (licença, português declarado, requisitos, instalação); atualize lá, não aqui.

Regras de escolha embutidas:

- Só entra modelo com licença de uso comercial confirmada. `--any-license` inclui os de uso pessoal (F5-TTS pt-BR, XTTS-v2) e os de licença não confirmada (Pocket TTS, Piper).
- Modelo de GPU só é recomendado se couber na VRAM livre. Placa de 4 GB fica no Kokoro em CPU: medimos um modelo de 1,7 B nessa faixa rodando 26 vezes mais lento que tempo real e morrendo por falta de memória.
- Requisito de VRAM de Chatterbox e Qwen3-TTS é estimativa nossa, porque os autores não publicam. Por isso o teste abaixo é obrigatório.

**Kokoro (integrado)**: `uv run <skill>/scripts/tts.py roteiro.txt -o public/audio/narration --voice pf_dora`. Vozes pt-BR: `pf_dora` (F), `pm_alex`, `pm_santa` (M). Inglês: `af_heart`, `af_bella`. Baixa cerca de 330 MB na primeira vez. `voice.py --bench` mede o fator de tempo real e o pico de RAM nesta máquina.

**Qualquer outro modelo**: instale com o comando que o `voice.py` mostra, num ambiente isolado. Antes do roteiro inteiro, gere **uma frase** com limite de tempo (`timeout 300 ...`) e confira três coisas: terminou, levou menos de 5x a duração do áudio e soa brasileiro para o usuário. Se falhar em qualquer uma, volte para o Kokoro. Depois gere o WAV completo e crie os tempos:

```bash
uv run <skill>/scripts/align.py public/audio/narration.wav roteiro.txt
```

## Tempos por palavra

| Origem | Tempos | Precisão |
|---|---|---|
| Kokoro | reais, por fonema e palavra | referência |
| ElevenLabs `with-timestamps` | reais, por caractere | referência |
| `align.py` (Whisper sobre o WAV) | reais | erro médio de 0,12 s no início da palavra, até 0,25 s, medido contra o Kokoro em pt-BR; tende a adiantar |
| OpenAI, Azure | estimados por tamanho da palavra (`approx: true`) | só para cena; rode `align.py` |

- Com `align.py`, use `<KineticWords lead={0}>`: o adiantamento do Whisper já faz o papel dos 3 frames de antecipação.
- `align.py` também confere a fala: `mismatch` conta palavras que o Whisper ouviu diferente do roteiro. Mais de 20% vira aviso e costuma ser pronúncia errada, texto trocado ou idioma errado (número e sigla escritos em forma curta também contam). Ele **não** distingue sotaque brasileiro de português europeu; isso só o ouvido do usuário decide.
- Voz gravada por uma pessoa segue o mesmo caminho: WAV mais `align.py`.

## Ritmo

- Calmo em pt-BR: 120 a 150 palavras por minuto (`--speed 0.88` a `0.95` no Kokoro). Acima de 170 o script avisa.
- Orçamento por cena: duração em segundos x 2,3 palavras. Corte texto, não acelere a voz. `lint.py` acusa cena acima de 2,6.
- Pausas: ponto final vira 0,35 s, vírgula 0,12 s. Para respiro maior, frases curtas.

## Normalização pt-BR (automática no `tts.py`)

- Expande R$ 1.234,56, 14h30, 10%, milhares, decimais e ordinais com `num2words`, corrigindo gênero (duas horas).
- Léxico em `assets/lexicon.pt-BR.json` para siglas e estrangeirismos (IA, CEO, SaaS). Nome de produto e de marca vai em um `lexicon.json` na pasta do vídeo, no mesmo formato, que soma ao da skill e vence em caso de conflito. O script lista termos suspeitos.
- Confira antes de gerar: `tts.py --normalize-only "texto"`.
- A tela mostra o texto original (`word`); a voz fala a forma normalizada (`spoken`).

## Saída

`narration.wav` e `narration.words.json`: `{text, duration, wpm, approx, words: [{word, spoken, start, end, ph}]}`. No Kokoro, o `end` de palavra com pontuação inclui a pausa que vem depois.

## Prosódia suave por provedor

- Kokoro: `--speed` e frases curtas.
- ElevenLabs: stability alta para constância; em `eleven_v3`, tags como `[warmly]` e `[softly]`.
- Azure: `<mstts:express-as style="calm">` e `<prosody rate="-8%">` (o script monta o SSML).
- OpenAI: `--instructions "voz calma, suave, acolhedora, ritmo pausado"`.
