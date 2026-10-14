# Roteiro, partitura e marcas

Um arquivo decide o tempo de tudo: `roteiro.json`, na raiz do projeto. `scripts/score.py` lê esse arquivo e escreve a voz (`public/audio/narration.wav`), a partitura (`public/timeline.json`) e as marcas (`public/cues.json`). Vídeo, mixagem, lint e QA leem a partitura; as cenas leem as marcas. Nenhum frame é escrito à mão em cena nenhuma.

```bash
uv run <skill>/scripts/score.py --dry     # o que seria gerado e quantos caracteres pagos
uv run <skill>/scripts/score.py --yes     # gera as frases novas, monta a voz, escreve partitura e marcas
uv run <skill>/scripts/score.py           # sem frase nova paga: refaz só os tempos (pausas, cortes, marcas, SFX)
```

Cada frase é um arquivo em `public/audio/seg/`, nomeado pelo hash do texto e da voz. Mudar pausa, corte ou SFX não gasta crédito. Trocar uma frase regera só aquela.

## Formato

```json
{
 "format": "reels",
 "fps": 30,
 "start": 0.3,
 "tail": 1.4,
 "voice": {"provider": "elevenlabs", "voice": "<voice_id>", "model": "eleven_multilingual_v2",
           "settings": {"stability": 0.4, "style": 0.5}, "seed": 7},
 "music": {"file": "audio/music.mp3", "gain_db": -15, "duck_db": -9, "offset": 12.0},
 "cut": {"on": "beat", "lead": 0.2, "sfx": {"type": "whoosh", "gain_db": -18, "dur": 0.5, "lead": 0.25}},
 "budget": {"full_renders": 4, "stills": 30},
 "scenes": [
  {"id": "gancho",
   "say": [{"text": "Seu caixa fecha sozinho.", "speak": "Seu caixa fecha sozinho!", "closed": true}],
   "cues": {"caixa": "word:caixa", "fecha": "word:fecha.end+0.1"},
   "sfx": [{"at": "caixa", "type": "pop", "gain_db": -15}]},
  {"id": "respiro", "beats": 4},
  {"id": "prova",
   "say": [{"text": "Em trinta segundos.", "pause": 0.5}, {"text": "Todo dia.", "at": 9.2}],
   "hold": 0.6}
 ]
}
```

| Campo | O que faz |
|---|---|
| `format` | `youtube`, `linkedin`, `reels`, `tiktok` ou `square`. No lugar dele vale `width` e `height` |
| `start`, `tail` | segundo em que a voz começa; quadro final depois da última palavra |
| `duration` | fixa a duração mínima; sem ele a duração sai da fala mais `tail` |
| `voice.provider` | `elevenlabs`, `kokoro`, `file` (voz que já existe) ou `none` |
| `voice.style` | marcação de entrega dos modelos v3 (`"[excited]"`); não é lida em voz alta |
| `music.offset` | pula os primeiros segundos da faixa (introdução longa) |
| `cut.on` | `phrase`: a cena abre `lead` segundos antes da fala. `beat`: o corte cai na batida anterior e a fala entra depois |
| `cut.sfx` | SFX automático em todo corte; `"cut_sfx": false` na cena desliga para aquela |
| `scenes[].say` | frases da cena. `text` é o que aparece na tela; `speak` é a grafia que ensina a pronúncia |
| `say[].pause` | silêncio antes da frase (padrão 0,35 s). `at` fixa o segundo absoluto em que ela começa |
| `say[].closed` | fim de bloco: a voz fecha a frase em vez de emendar a entonação na seguinte |
| `scenes[].dur` ou `beats` | duração de cena sem fala, em segundos ou em batidas da trilha |
| `scenes[].hold` | segundos de respiro depois da última fala da cena (padrão 0,3) |

## Marcas (`cues`)

Uma marca é um nome para um instante. O valor é uma expressão resolvida dentro da cena:

| Expressão | Instante |
|---|---|
| `word:caixa` | início da palavra na fala da cena. `word:voz#2` é a segunda ocorrência |
| `word:caixa.end+0.1` | fim da palavra, mais 0,1 s. O sufixo `.end` e o deslocamento valem para todas |
| `phrase:2` | início da segunda frase da cena |
| `scene`, `scene.end-0.5` | início e fim da cena |
| `beat:3` | terceira batida da trilha a partir do início da cena |
| `cue:caixa+0.4` | outra marca já definida, mais um deslocamento |
| `t:12.5` | segundo absoluto do vídeo |
| `1.2` (número) | segundos a partir do início da cena |

Os nomes são globais e caem no frame exato. O SFX aponta para a marca (`"at": "caixa"`) ou para uma expressão: imagem e som saem do mesmo número.

## Nas cenas

```tsx
import {Scene, useScene, WORDS} from '../lib/score';

const Gancho: React.FC = () => {
	const {frame, len, at, since} = useScene('gancho');
	const entra = pop(frame, 30, at('caixa'));            // começa quando a voz diz "caixa"
	const sai = tween(frame, len - 10, 10, 0, 1, ease.exit);
	...
};
// na composição:  <Scene id="gancho"><Gancho /></Scene>
```

`useScene(id)` devolve `frame` local, `len`, `at('marca', deslocamentoEmFrames)`, `sec(segundoAbsoluto)`, `since('marca')` e `words` (as palavras ditas na cena). `WORDS` tem todas, em tempo absoluto, para `<KineticWords>` e para o bloco `<Captions>`.

## Voz que já existe (gravada, de outro modelo ou a fala de uma filmagem)

1. Tempos por palavra: `align.py voz.wav roteiro.txt`, ou `align.py filmagem.mp4 --transcribe -o public/audio/fala` quando não há roteiro. Leia o `.txt`, corrija a grafia e rode de novo com ele como roteiro.
2. No roteiro: `"voice": {"provider": "file", "file": "audio/fala.wav", "start": 0}`. As frases de `say` precisam bater palavra por palavra com o que foi dito; o script acusa a primeira que não bate.
3. Os tempos das frases ficam fixos (a fala já existe). Marcas, cortes e SFX funcionam igual.

## Sem voz

`"voice": {"provider": "none"}` e cenas com `dur` ou `beats`. Com `cut.on: "beat"` os cortes caem na grade da trilha: rode `beats.py` antes, ele escreve `<trilha>.beats.json` ao lado do arquivo.

## Limites

- `score.py` gera voz só com ElevenLabs e Kokoro. Outro provedor: gere o WAV, alinhe e use `provider: file`.
- Com `provider: file` não há pausa ajustável: o áudio é o que foi gravado.
- A checagem de fala cortada (pontas limpas, buraco no meio, texto falado igual ao escrito) foi calibrada em pt-BR com dois modelos da ElevenLabs. Ouça o `mix.wav` antes de animar.
