#!/usr/bin/env node
/* Render por cena, com remendo do master, vários formatos numa rodada e orçamento de renders.

  node <skill>/scripts/render.cjs Showcase                          render completo -> out/render.mp4
  node <skill>/scripts/render.cjs Showcase --scene fecho,abre       refaz só essas cenas e remonta o master
  node <skill>/scripts/render.cjs Showcase --formats reels,square,youtube     -> out/render-<formato>.mp4
  node <skill>/scripts/render.cjs Showcase --draft                  meia escala em out/draft.mp4, fora do orçamento
  node <skill>/scripts/render.cjs Showcase --remux                  só o áudio mudou: remonta o master sem renderizar nada
Rode na pasta do projeto, depois do mix.py. Um bundle e um browser servem todas as cenas. Cada cena da partitura
vira um trecho em out/seg/<formato>/; o master é a emenda dos trechos sem reencode, com o áudio de timeline.audio.
--scene reaproveita os trechos das outras cenas se o intervalo de frames delas não mudou. Mudou código que várias
cenas usam (tema, componente, bloco)? Rode sem --scene: o remendo só sabe o que você diz que mudou.
Orçamento: budget.full_renders da partitura (padrão 4). Estourou, o script recusa; --over "motivo" libera e o
motivo fica em out/ledger.json. Usa o backend gráfico de out/gl.json (rode gl.py uma vez por projeto).
*/
const fs = require('fs');
const path = require('path');
const {createRequire} = require('module');
const {execFileSync} = require('child_process');

const args = process.argv.slice(2);
const opt = (name, def) => {
	const i = args.indexOf(`--${name}`);
	return i >= 0 ? args[i + 1] : def;
};
const flag = (name) => args.includes(`--${name}`);
const fail = (msg) => {
	console.error(msg);
	process.exit(1);
};
const comp = args[0] && !args[0].startsWith('--') ? args[0] : null;
if (!comp) fail('uso: node render.cjs <Composição> [--scene id,id] [--formats reels,square,youtube] [--draft] [--remux] [--over "motivo"] [--props json] [--concurrency n]');

const proj = process.cwd();
const req = createRequire(path.join(proj, 'package.json'));
let bundler, renderer;
try {
	bundler = req('@remotion/bundler');
	renderer = req('@remotion/renderer');
} catch (e) {
	fail('não achei @remotion/bundler e @remotion/renderer no projeto: rode npm install na pasta do vídeo');
}
const entry = ['src/index.ts', 'src/index.tsx', 'src/index.js', 'src/index.jsx'].map((p) => path.join(proj, p)).find((p) => fs.existsSync(p));
if (!entry) fail('não achei src/index.ts na pasta atual');
const tlFile = path.resolve(opt('timeline', 'public/timeline.json'));
const tl = JSON.parse(fs.readFileSync(tlFile, 'utf8'));
const draft = flag('draft');
const remux = flag('remux');
const only = opt('scene') ? opt('scene').split(',') : null;
const formats = opt('formats') ? opt('formats').split(',') : [null];
const baseProps = JSON.parse(opt('props', '{}'));
for (const id of only || []) if (!tl.scenes.some((s) => s.id === id)) fail(`cena "${id}" não existe na partitura (${tl.scenes.map((s) => s.id).join(', ')})`);

const ledgerFile = path.join(proj, 'out/ledger.json');
const ledger = fs.existsSync(ledgerFile) ? JSON.parse(fs.readFileSync(ledgerFile, 'utf8')) : [];
const budget = (tl.budget || {}).full_renders || 4;
const spent = ledger.filter((e) => e.kind === 'full').length;
const full = !only && !draft && !remux;
if (full && spent >= budget && !opt('over')) {
	fail(`orçamento: ${spent} renders completos já feitos, teto ${budget}. Confira nos stills (stills.cjs) ou refaça só a cena (--scene id). Para seguir mesmo assim: --over "motivo"`);
}

let gl = opt('gl', null);
const glFile = path.join(proj, 'out/gl.json');
if (!gl && fs.existsSync(glFile)) gl = JSON.parse(fs.readFileSync(glFile, 'utf8')).gl || null;
const ff = (a) => execFileSync('ffmpeg', ['-v', 'error', '-y', ...a], {stdio: ['ignore', 'ignore', 'inherit']});

(async () => {
	const t0 = Date.now();
	const serveUrl = await bundler.bundle({entryPoint: entry, publicDir: path.join(proj, 'public')});
	// O bundle copia a pasta public inteira para o temporário do sistema: sem isto, cada rodada deixa centenas de MB para trás.
	process.on('exit', () => {
		try {
			fs.rmSync(serveUrl, {recursive: true, force: true});
		} catch (e) {}
	});
	const browser = await renderer.openBrowser('chrome', {logLevel: 'error', ...(gl ? {chromiumOptions: {gl}} : {})});
	const outputs = [];
	let frames = 0;
	for (const format of formats) {
		const inputProps = {...baseProps, ...(format ? {format} : {})};
		const composition = await renderer.selectComposition({serveUrl, id: comp, puppeteerInstance: browser, inputProps});
		const {fps, durationInFrames} = composition;
		const dir = path.join(proj, 'out/seg', draft ? 'draft' : format || 'main');
		fs.mkdirSync(dir, {recursive: true});
		const manFile = path.join(dir, 'manifest.json');
		const man = fs.existsSync(manFile) ? JSON.parse(fs.readFileSync(manFile, 'utf8')) : {};
		const done = [];
		const list = [];
		for (const [i, s] of tl.scenes.entries()) {
			const a = Math.round(s.start * fps);
			const b = Math.min(i + 1 < tl.scenes.length ? Math.round(tl.scenes[i + 1].start * fps) : durationInFrames, durationInFrames) - 1;
			const file = path.join(dir, `${String(i).padStart(2, '0')}_${s.id}.mp4`);
			const same = man[s.id] && man[s.id].a === a && man[s.id].b === b && fs.existsSync(file);
			if (remux && !same) fail(`--remux: o trecho da cena ${s.id} não existe ou mudou de intervalo; rode sem --remux`);
			if (!remux && (!only || only.includes(s.id) || !same)) {
				if (only && !only.includes(s.id)) console.error(`cena ${s.id}: intervalo de frames mudou, refazendo também`);
				await renderer.renderMedia({
					composition, serveUrl, codec: 'h264', outputLocation: file, frameRange: [a, b], muted: true, inputProps,
					colorSpace: 'bt709', puppeteerInstance: browser, logLevel: 'error', scale: draft ? 0.5 : 1,
					...(opt('concurrency') ? {concurrency: Number(opt('concurrency'))} : {}), ...(gl ? {chromiumOptions: {gl}} : {}),
				});
				man[s.id] = {a, b};
				done.push(s.id);
				frames += b - a + 1;
			}
			list.push(`file '${file.replace(/'/g, "'\\''")}'`);
		}
		for (const id of Object.keys(man)) if (!tl.scenes.some((s) => s.id === id)) delete man[id];
		fs.writeFileSync(manFile, JSON.stringify(man, null, 1));
		fs.writeFileSync(path.join(dir, 'list.txt'), list.join('\n'));
		const out = path.join(proj, 'out', draft ? `draft${format ? `-${format}` : ''}.mp4` : `render${format ? `-${format}` : ''}.mp4`);
		const audio = tl.audio ? path.join(path.dirname(tlFile), tl.audio) : null;
		const mux = ['-f', 'concat', '-safe', '0', '-i', path.join(dir, 'list.txt')];
		if (audio && fs.existsSync(audio)) {
			// O AAC devolve picos acima do WAV (medido: até 2 dB em fala muito amplificada). Um limitador 1 dB abaixo
			// do teto do mix segura o pico do MP4 dentro do que o qa.py cobra, sem mexer no loudness.
			const tp = ((tl.loudness || {}).tp ?? -3) - 1;
			mux.push('-i', audio, '-map', '0:v:0', '-map', '1:a:0', '-af', `alimiter=limit=${Math.pow(10, tp / 20).toFixed(3)}:attack=5:release=80:level=false`, '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', String(durationInFrames / fps));
		}
		else console.error('sem áudio: timeline.audio não existe (rode mix.py antes)');
		ff([...mux, '-c:v', 'copy', '-movflags', '+faststart', out]);
		outputs.push({format: format || 'partitura', out: path.relative(proj, out), cenas_refeitas: done, cenas_reaproveitadas: tl.scenes.length - done.length});
	}
	await browser.close({silent: true});
	const sec = Math.round((Date.now() - t0) / 100) / 10;
	ledger.push({at: new Date().toISOString(), kind: draft ? 'draft' : remux ? 'remux' : full ? 'full' : 'scene', composition: comp, formats: formats.filter(Boolean), scenes: only, frames, sec, ...(opt('over') ? {over: opt('over')} : {})});
	fs.mkdirSync(path.dirname(ledgerFile), {recursive: true});
	fs.writeFileSync(ledgerFile, JSON.stringify(ledger, null, 1));
	console.log(JSON.stringify({outputs, frames, sec, gl: gl || 'padrão', renders_completos: `${spent + (full ? 1 : 0)} de ${budget}`}));
	process.exit(0);
})().catch((e) => fail(e && e.stack ? e.stack : String(e)));
