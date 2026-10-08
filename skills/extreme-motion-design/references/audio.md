# Áudio: trilha, SFX, sincronia e loudness

## Licença (regra que bloqueia)

- Aceite só `cc0`, `pdm` e `by`, ou áudio gerado. Em CC 4.0, música sincronizada com imagem é obra adaptada: `by-nd` não pode entrar no vídeo e `by-sa` obriga a licenciar o vídeo em `by-sa`. `nc` e sampling+ ficam fora.
- Fontes que não servem para download por script: Pixabay (API sem áudio), Mixkit e Uppbeat (termos proíbem automação), Free Music Archive (proíbe requisição automatizada). Freesound e Jamendo: API grátis só para uso não comercial.
- `music.py` grava `credits.json` ao lado do arquivo: título, autor, URL, licença, data da verificação, texto de atribuição e modificações. Cole o campo `attribution` na descrição do vídeo.

## Cadeia de trilha

1. Incompetech (Kevin MacLeod, CC BY 4.0, catálogo com BPM): `music.py incompetech --feel calm --bpm 70-110 --min-sec 60`.
2. Openverse com licença filtrada: `music.py openverse --q "ambient piano"`. Sem token: limite baixo por hora.
3. Geração local offline: `music.py generate --sec 30 --bpm 84 --mood calm|uplift|tense`. Cama simples e limpa, boa para fundo de narração.
4. Opcional, com acordo do usuário: ElevenLabs Music (`POST /v1/music`, `force_instrumental`), Stable Audio 3 Small (local, licença Stability Community para receita abaixo de US$ 1 milhão por ano), ACE-Step 1.5 (MIT, pede GPU).

## SFX

- Procedurais e instantâneos: `sfx.py` gera whoosh, swoosh, riser, impact, click, pop, tick e shimmer. Sem licença de terceiros.
- Declare na partitura: `{"at": 3.2, "type": "whoosh", "gain_db": -15, "dur": 0.5}`; `mix.py` posiciona no tempo exato.
- Onde colocar: whoosh centrado no corte (começa 0,25 s antes), pop quando uma forma assenta, click no frame do clique, riser nos 1 a 2 s antes do clímax, impact no clímax. Menos é mais: 1 SFX por evento com significado.
- Biblioteca maior: Sonniss GDC (royalty-free, sem atribuição) baixada uma vez pelo usuário e indexada localmente.

## Sincronia

- Com narração, a voz é o relógio: cenas começam 0,2 s antes da frase.
- Música rítmica: `beats.py` e corte nos downbeats (`downbeat_frames`). Música calma não tem grade confiável: corte por frase.
- Use um único analisador de batidas no projeto.

## Mixagem e loudness

- Níveis de partida: narração 0 dB, trilha -14 a -18 dB com ducking de -10 dB sob a voz, SFX -12 a -17 dB.
- `mix.py` faz ducking por envelope da voz (ataque 20 ms, release 400 ms) e normalização em duas passadas com ffmpeg `loudnorm`.
- Alvos: YouTube, Reels, TikTok e LinkedIn -14 LUFS e true peak -1 dBTP (convenção de mercado; as plataformas não publicam alvo oficial, exceto o volume estável do YouTube). Podcast Apple -16 LUFS. O padrão da partitura é -14 LUFS e -1,5 dBTP.
