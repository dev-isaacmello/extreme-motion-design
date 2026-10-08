# Narração: voz suave, pt-BR e tempos por palavra

## Cadeia

| Uso | Provedor | Vozes suaves | Tempos |
|---|---|---|---|
| Padrão grátis, local, CPU | Kokoro-82M (`kokoro-onnx`, Apache-2.0) | pt-BR: `pf_dora` (F), `pm_alex`, `pm_santa` (M). Inglês: `af_heart`, `af_bella` | Reais, por fonema e palavra |
| Premium | ElevenLabs `eleven_multilingual_v2` ou `eleven_v3` | busque na Voice Library com filtro de idioma portuguese e sotaque brasileiro | Reais, por caractere |
| Custo baixo com estilo | Azure `pt-BR-FranciscaNeural` estilo `calm` | `pt-BR-ThalitaNeural`, `pt-BR-AntonioNeural` | Estimados via REST |
| Direção por texto | OpenAI `gpt-4o-mini-tts` | `marin`, `cedar` com `instructions` | Estimados |

- O Kokoro baixa ~330 MB do GitHub na primeira vez (`~/.cache/motion-design/kokoro`, ou `KOKORO_DIR`). Gera 1 minuto de áudio em cerca de 40 s de CPU com 2 núcleos.
- A qualidade das vozes pt-BR do Kokoro não tem nota oficial: gere um trecho de 10 s com cada voz e escolha ouvindo. Se o usuário quiser voz de estúdio, sugira ElevenLabs e peça a chave.
- Antes de usar API paga, confirme com o usuário. Para ElevenLabs, evite as vozes Default (expiram em 31/12/2026, segundo a documentação).

## Ritmo

- Calmo em pt-BR: 120 a 150 palavras por minuto (`--speed 0.88` a `0.95` no Kokoro). Acima de 170 o script avisa.
- Orçamento de palavras por cena: duração da cena em segundos x 2,3. Corte texto, não acelere a voz.
- Pausas: ponto final vira 0,35 s, vírgula 0,12 s. Para respiro maior, quebre em frases curtas.

## Normalização pt-BR (automática no `tts.py`)

- Expande R$ 1.234,56, 14h30, 10%, milhares, decimais e ordinais com `num2words`, corrigindo gênero (duas horas).
- Léxico editável em `assets/lexicon.pt-BR.json` para siglas e estrangeirismos (IA, CEO, SaaS, YouTube, nomes de produto). O script lista termos suspeitos; adicione os que soarem errados.
- Confira antes de gerar: `tts.py --normalize-only "texto"`.
- A tela mostra o texto original (`word`); a voz fala a forma normalizada (`spoken`). Os tempos valem para os dois.

## Saída

`narration.wav` e `narration.words.json`: `{text, duration, wpm, approx, words: [{word, spoken, start, end, ph}]}`. Com `approx: true` os tempos são estimados por tamanho de palavra: bons para cenas, fracos para karaokê. Para karaokê com provedor sem tempos, alinhe depois com ElevenLabs Forced Alignment ou WhisperX (`load_align_model(language_code="pt")`).

## Prosódia suave por provedor

- Kokoro: `--speed` e frases curtas.
- ElevenLabs v3: tags como `[warmly]`, `[softly]` e reticências; stability alta para constância.
- Azure: `<mstts:express-as style="calm">` e `<prosody rate="-8%">` (o script monta o SSML).
- OpenAI: `--instructions "voz calma, suave, acolhedora, ritmo pausado"`.
