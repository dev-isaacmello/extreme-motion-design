# Extreme Motion Design

A motion design skill for coding agents (Claude, Claude Code, Codex and anything that reads `SKILL.md`). The agent writes the video as code with Remotion and React, with voice, licensed music and synced sound effects, and it is not allowed to deliver until the frames have been measured.

[Leia em português](README.pt-BR.md)

<p align="center">
  <img src="docs/media/apresentacao-2.0.gif" width="720" alt="Excerpt of the 2.0 presentation film: the title over a rocket launch, 2D, 2.5D and 3D scenes, cuts on public domain footage, five styles, the measured gate and the closing title">
</p>

The film above is the 2.0 presentation, made with the skill. Every number on screen was measured and the imagery is public domain or CC0 (NASA, USGS, NPS and The Met), fetched by the skill with the licence checked per file.

## What is new in 2.0

- **Reference mode.** Hand it a video and `reference.py` breaks it into measured structure (shots, camera moves, palette, where the visual mass sits, audio), writes a script skeleton with the same timings, and scores the new piece from 0 to 100 against the reference. Calibration: the piece against itself scores 100, using the score boundaries as cuts 86, a reel made from the same request without the reference 38, unrelated videos 23 and 24. It copies structure, rhythm and technique. It never copies frames, assets, text or sound.
- **A design meter.** `design.py` counts the signals of the frame a model produces with no direction: near black with one accent, a giant condensed face on the left margin, decorative mono, everything in caps, the same composition in every scene. It flagged my own 1.3 reel (4 signals) and the template example (3). The 2.0 film scores 0.
- **A design reference.** `references/design.md` covers composition, type, colour, texture, real imagery and launch film structure, each rule with its source, plus six named art directions to propose from.
- **Real imagery with the licence checked.** `stock.py` fetches photo and video from Wikimedia Commons (CC0 and public domain only), NASA, Openverse and The Met, and records the evidence read from the API for every file.
- **Face and hand tracking** in `track.py`, for graphics pinned to a body.

## Why it exists

An agent writing video code cannot see what it renders. Left alone it ships text cut by the frame edge, captions over a face, the same card sliding into every scene, and audio that clips. I built the skill around that blind spot:

- **The audio is the clock.** One `roteiro.json` produces the voice phrase by phrase, the score and the named cues. No scene holds a hand typed frame number.
- **The direction is a contract.** Before any scene exists the piece declares its concept, its visual law, its motif and the layout and entrance of every scene. The lint rejects a project without it, and rejects one where every scene is laid out the same way.
- **The text is measured, not eyeballed.** A probe reads every text box from the DOM of each still and the background from the pixels. Cut off, overlapping, too small, low contrast or outside the safe area fails.
- **Someone else reviews.** The contact sheet goes to a reviewer with a clean context that never saw the code.
- **The final file passes a numeric gate.** Codec, loudness, true peak, flashes per second, one frame pops, loop seam, contrast against the stills.

## What the gates caught while making this reel and a second one built on phone footage

These are real lines from the session, not examples I wrote for the README.

| Gate | What it said | What was wrong |
|---|---|---|
| `layout.py` | `"renderizando 90%" x "milho": dois textos sobrepostos` | A label sat on top of the captions |
| `layout.py` | `letra de 9 px: mínimo legível é 20 px neste formato` | A chip was captured while scaling in from zero |
| `layout.py` | `"Extreme": texto cortado pela borda do quadro` | A 300 px headline ran off the right edge |
| `layout.py` | `"Cor,": contraste 2.9:1 (texto #ff4b1f sobre #f3eee5)` | Orange type on cream paper |
| `qa.py` | `true peak: -0.1 dBTP (máx -1.0)` | AAC encoding raised the peaks of a boosted voice |
| `qa.py` | `flashes por segundo <= 3: pior janela: 4` | A five colour burst flickered |
| reviewer | "FAIL turns into PASS with the same measured value" | The checklist scene contradicted itself |
| reviewer | "EDIÇAO is missing its tilde" | The reveal mask clipped accents in a condensed font |

Every one of them was fixed before delivery, and four of them became fixes in the skill itself.

## The same request without the skill

I ran the same request through the same model with the skill forbidden, plain Remotion only, and no paid voice. It is the honest comparison, so here it is with what I measured.

<p align="center">
  <img src="docs/media/sem-skill.gif" width="230" alt="The same request without the skill">
  <img src="docs/media/reel-manifesto.gif" width="230" alt="The same request with the skill">
</p>

| | Without the skill | With the skill |
|---|---|---|
| Time to a file | about 8 minutes, 1 render | several times longer, 1 full render plus 1 scene patch |
| Look | strong, and close to the one on the right | strong |
| Voice | none | narration with real word timings, and the cuts follow it |
| Music | a raw ffmpeg synth the agent itself called the weakest point | a CC BY track with the credit recorded, ducked under the voice |
| Loudness | -12.5 LUFS, fails the -14 target | -14, true peak under -1 dBTP |
| Colour tag | none | BT.709 |
| Text and safe area | a headline cut by the right edge mid scene, the frame readout at y 118 under the app interface | measured on every still, 0 failures at delivery |
| Numbers on screen | "frame 105" in the checklist is invented | the counter shows the real frame and the checklist shows real measurements |
| Independent review | none | 16 of 21 frames sent back as FIX; the real defects were fixed, the ones that were mid transition were not |

What I take from it: a good model already makes a good looking frame without help. The skill does not buy taste. It buys sound, a clock, measured text, true numbers and a second pair of eyes, and it costs time.

## Gallery

| | Prompt | Notes |
|---|---|---|
| <img src="docs/media/apresentacao-2.0.gif" width="320"> | "Something in every dimension and style, alternating between the real world and not, editing worthy of cinema, modern typography, an animated voice." | ElevenLabs voice (`eleven_v4`), 11 scenes, 68 s, public domain and CC0 imagery, `design.py` verdict: own direction, 0 signals. The music was composed with ElevenLabs Music by a script outside the skill, since `music.py` does not support it. 4 full renders and 1 scene patch |
| <img src="docs/media/reel-manifesto.gif" width="180"> | "A very extravagant 9:16 reel, about 25 s, presenting the skill as a manifesto: this is not editing, it is code." | ElevenLabs voice, cuts on the beat of a CC BY track, 3D scene, real frame counter. [Source](examples/reel-manifesto). 1 full render and 1 scene patch |
| <img src="docs/media/apresentacao.gif" width="320"> | "Present the skill itself in 90 s, technique by technique." | Made with version 1.1, 11 scenes |
| <img src="docs/media/template.gif" width="320"> | none | The example that ships in the template, generated by `score.py` with the local voice |

## Install

### Claude Code (plugin)

```
/plugin marketplace add dev-isaacmello/extreme-motion-design
/plugin install extreme-motion-design@extreme-motion-design
```

### Claude Code, Codex, Cursor and others (skills CLI)

```bash
npx skills add dev-isaacmello/extreme-motion-design
```

### Claude (claude.ai and the desktop app)

```bash
git clone https://github.com/dev-isaacmello/extreme-motion-design
cd extreme-motion-design/skills
zip -r extreme-motion-design.zip extreme-motion-design/
```

Upload the zip in **Customize > Skills**. The zip must have the `extreme-motion-design/` folder at the top.

### Updating

- Plugin: `claude plugin update extreme-motion-design@extreme-motion-design` and restart.
- skills CLI: run `npx skills add` again.
- claude.ai: remove the old skill and upload the new zip.

## Use

Ask in plain language. The skill instructions are written in Portuguese and the agent follows them in any language.

```
a 20 second 16:9 video with a calm pt-BR narration presenting our annual plan launch
```

```
a 9:16 reel from this phone video, with the caption following my hand
```

```
animate this logo in 4 seconds and loop it seamlessly
```

## How a video is made

| Step | What happens |
|---|---|
| Brief | Goal, audience, format, duration, tone and brand in five lines |
| Brand | `brand.py` extracts colours, fonts and logo from a site, a repository or screenshots, with the origin of each value. Nothing is invented: what is not found stays empty |
| Voice | `voice.py` measures the hardware and the agent asks: no voice, ElevenLabs, or a local model that fits the machine |
| Direction | Two or three directions as styleframes, the user picks, and the choice is written to `direction.json` |
| Score | `score.py` turns `roteiro.json` into voice, `timeline.json` and `cues.json`. Each phrase is cached by hash, so changing a pause or a cut costs nothing and changing one phrase regenerates only that phrase |
| Music and SFX | `music.py` fetches a track with a verified licence or generates one locally. `sfx.py` synthesises the effects. `mix.py` ducks the music under the voice |
| Scenes | 15 ready blocks (charts, counter, device frame, captions, code window, cursor, lower third and more) plus primitives for camera, morph, rig, kinetic type, tracking |
| Lint | `lint.py` checks the direction contract, the score and the code in under a second |
| Dailies | `stills.cjs` renders the key frames in one process, `layout.py` measures the text, `contact_sheet.py` builds the sheet |
| Review | A subagent with a clean context retells the message from the frames alone and marks each frame PASS or FIX |
| Render | `render.cjs` renders scene by scene, patches a single scene without a full render, and outputs reels, square and landscape from the same composition |
| Gate | `qa.py` on the final file. No FAIL, or no delivery |

Techniques covered: keyframing, easing and springs, camera moves and parallax, kinetic typography, morphing, seamless loops, UI micro interactions, anticipation, overshoot, squash and stretch, smear, speed ramps, match cuts, shape and liquid transitions, mattes, frame by frame, cel animation, stop motion, rigging with IK, lip sync, 3D, compositing, point, plane, face and hand tracking, match moving and rotoscoping.

## Requirements

- Node 18 or newer.
- Python 3.10 or newer. Scripts declare their dependencies inline (PEP 723) and run with `uv run`.
- ffmpeg on the PATH.

## Remotion licence

The skill is MIT. Remotion, which renders the video, is source available and not open source. Read this before adopting the skill at work:

- Free for individuals, for companies with up to 3 employees, for non profits and for evaluation.
- From 4 people on, a Company License is required. At the time I checked (2026-10-13) a seat cost US$ 25 per month and a seat is needed for each person who writes Remotion code, including through a coding agent.
- A freelancer or agency that hands over only the final file counts its own headcount. If the client operates the project, the headcounts add up.
- The draft terms for Remotion 5.0 say contractors will count towards team size. 5.0 was not released when I checked.

Sources: [LICENSE.md](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md), [licence FAQ](https://www.remotion.dev/docs/license/faq), [pricing](https://www.remotion.pro/license). The skill warns the user when the company has more than 3 people.

## What the skill runs and accesses

- `npm install` in the video project (Remotion, React, Three from the npm registry).
- `uv run` on the scripts in `scripts/`, which installs the Python dependencies each file declares.
- `voice.py` reads threads, RAM, disk and GPU (`nvidia-smi`). With `--check-key` it makes one read request to `api.elevenlabs.io`.
- `score.py` and `tts.py` send the script to ElevenLabs only when that voice was chosen, using the key in the project `.env`. `score.py --dry` prints the character count first and the paid run needs `--yes`.
- `tts.py` downloads the Kokoro voice model (about 330 MB) and `align.py` downloads Whisper `small` (about 460 MB) on first use.
- `track.py --face` downloads YuNet (230 KB) and `--hand` downloads the MediaPipe hand model (7.5 MB). `roto.py --backend rembg` downloads its segmentation model.
- `music.py` queries Incompetech and Openverse.
- `stock.py` queries Wikimedia Commons, the NASA image library, Openverse and The Met, and Pixabay only when you put a key in `.env`. It downloads the file you pick and strips the audio track of videos.
- `reference.py` only reads the video file you give it. It does not download from any platform.
- `brand.py --url` fetches the page you name and the stylesheets, fonts and images that page references, and takes two screenshots with a local headless Chrome. `--repo` only reads files.
- Nothing else is contacted.

## Limits

- The agent reviews still frames and numbers. Rhythm and the feel of the motion still need a human eye before publishing.
- The layout probe only sees DOM text. Text drawn on canvas, in WebGL or inside an image is not measured, and text covered by another opaque layer is measured as if it were visible.
- Scene similarity compares 24x24 grey thumbnails. It was calibrated on six videos (medians from -0.08 to 0.71) and I had no repetitive video to calibrate the warning threshold against, so it is conservative.
- The fidelity score measures structure, not quality or content, and its tempo reading is unreliable when a voice sits over the music.
- The design meter thresholds come from practice and were calibrated on a handful of videos. Its verdict is a warning, not a gate.
- A free licence covers copyright only. Recognisable people, trademarks and recent artworks still need permission, and `stock.py` cannot detect them.
- `brand.py` picks the accent colour by heuristic. On a monochrome brand it can be wrong or empty, and it says so.
- Face tracking fails on profiles and on faces looking down. Hand tracking loses fast gestures.
- `render.cjs --scene` only knows what you tell it changed. After editing shared code, render everything.
- The rhythm warnings of `qa.py` and `lint.py` are heuristics tuned on a few videos.
- Only Kokoro is integrated as a local voice. The other models in `assets/tts-models.json` are recommendations by licence and memory.
- The skill instructions are in Portuguese.

## Licence

MIT
