#!/usr/bin/env node
/* Stills em lote: um bundle e um browser para todos os frames (a CLI refaz os dois a cada `remotion still`).

  node <skill>/scripts/stills.cjs Showcase --timeline public/timeline.json     início, meio e fim de cada cena
  node <skill>/scripts/stills.cjs Showcase --times 1.2,3.5,7                   instantes em segundos
  node <skill>/scripts/stills.cjs Showcase --frames 45,90 --scale 1 --out out/sf
Rode na pasta do projeto. Grava f<frame>.png e index.json em --out (padrão out/stills); a folha de contato
sai de `contact_sheet.py --stills out/stills`, sem precisar de MP4. Usa o backend de out/gl.json quando existir.
*/
const fs = require('fs');
const path = require('path');
const {createRequire} = require('module');

const args = process.argv.slice(2);
const opt = (name, def) => {
	const i = args.indexOf(`--${name}`);
	return i >= 0 ? args[i + 1] : def;
};
const comp = args[0] && !args[0].startsWith('--') ? args[0] : null;
const proj = process.cwd();
const out = path.resolve(opt('out', 'out/stills'));
const scale = Number(opt('scale', '0.5'));
const par = Number(opt('parallel', '4'));

const fail = (msg) => {
	console.error(msg);
	process.exit(1);
};
if (!comp) fail('uso: node stills.cjs <Composição> [--timeline arquivo | --times s,s | --frames n,n] [--scale 0.5] [--out out/stills] [--gl backend]');

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

let gl = opt('gl', null);
const glFile = path.join(proj, 'out/gl.json');
if (!gl && fs.existsSync(glFile)) gl = JSON.parse(fs.readFileSync(glFile, 'utf8')).gl || null;

(async () => {
	const serveUrl = await bundler.bundle({entryPoint: entry, publicDir: path.join(proj, 'public')});
	const browser = await renderer.openBrowser('chrome', gl ? {chromiumOptions: {gl}} : {});
	const composition = await renderer.selectComposition({serveUrl, id: comp, puppeteerInstance: browser});
	const {fps, durationInFrames} = composition;

	let times;
	if (opt('frames')) {
		times = opt('frames').split(',').map((f) => Number(f) / fps);
	} else if (opt('times')) {
		times = opt('times').split(',').map(Number);
	} else {
		const tl = JSON.parse(fs.readFileSync(path.resolve(opt('timeline', 'public/timeline.json')), 'utf8'));
		times = tl.scenes.flatMap((s) => [s.start + 0.15, (s.start + s.end) / 2, s.end - 0.15]);
	}
	const frames = [...new Set(times.map((t) => Math.min(Math.max(Math.round(t * fps), 0), durationInFrames - 1)))];

	fs.mkdirSync(out, {recursive: true});
	for (const f of fs.readdirSync(out)) if (/^f\d+\.png$/.test(f) || f === 'index.json') fs.unlinkSync(path.join(out, f));
	const index = frames.map((frame) => ({frame, t: Number((frame / fps).toFixed(3)), file: `f${String(frame).padStart(5, '0')}.png`}));
	let next = 0;
	await Promise.all(
		Array.from({length: Math.max(1, Math.min(par, index.length))}, async () => {
			while (next < index.length) {
				const it = index[next++];
				await renderer.renderStill({composition, serveUrl, frame: it.frame, scale, output: path.join(out, it.file), puppeteerInstance: browser});
			}
		}),
	);
	await browser.close({silent: true});
	fs.writeFileSync(path.join(out, 'index.json'), JSON.stringify({composition: comp, fps, scale, stills: index}, null, 1));
	console.log(JSON.stringify({out: path.relative(proj, out), stills: index.length, gl: gl || 'padrão'}));
	process.exit(0);
})().catch((e) => fail(e && e.stack ? e.stack : String(e)));
