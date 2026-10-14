import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame} from 'remotion';
import timeline from '../../public/timeline.json';
import {CodeWindow} from '../blocks/CodeWindow';
import {Marquee} from '../blocks/Marquee';
import {Rise, trim} from '../blocks/shared';
import {Grain, IrisReveal} from '../components/Fx';
import {morphPath} from '../components/Morph';
import {Probe} from '../components/Probe';
import {ease, easeX, keys, pop, springs, squash, tween} from '../lib/motion';
import {BEATS, Scene, sceneOf, useScene} from '../lib/score';
import {blobPath, circlePath, roundedRectPath, starPath} from '../lib/shapes';
import {C, DISPLAY, FONT, MONO} from '../theme';
import {Shapes3D} from './Shapes3D';

const W = 1080;
const H = 1920;
const big: React.CSSProperties = {fontFamily: DISPLAY, fontWeight: 400, lineHeight: 0.9, letterSpacing: '-0.01em', textTransform: 'uppercase'};
const pad4 = (n: number) => String(Math.max(0, n)).padStart(4, '0');

/** Motivo da peça: o contador de frames. Em toda cena ele diz a verdade (o frame que está na tela) e a cada cena tem outro papel. */
const TOTAL = Math.round(timeline.duration * timeline.fps);
const BURST = 14;
const Counter: React.FC<{color: string; id: string}> = ({color, id}) => {
	// Dentro de <Scene> o frame é local: soma o início da cena para mostrar o frame real do vídeo.
	const frame = useCurrentFrame() + Math.round(sceneOf(id).start * timeline.fps);
	const durationInFrames = TOTAL;
	return (
		<div style={{position: 'absolute', right: 108, top: 372, fontFamily: MONO, fontSize: 36, fontWeight: 700, color, fontVariantNumeric: 'tabular-nums'}}>
			f {pad4(frame)} / {pad4(durationInFrames)}
		</div>
	);
};

/** Cena 1: preto, tipografia gigante empilhada. A palavra "não" é o único ponto de cor. */
const Nao: React.FC = () => {
	const {frame, at} = useScene('nao');
	const strike = tween(frame, at('edicao') + 7, 9, 0, 1, ease.sharp);
	const no = pop(frame, 30, at('nao') - 1, springs.snappy);
	return (
		<AbsoluteFill style={{background: C.bg, color: C.ink}}>
			<Counter color={C.muted} id="nao" />
			<div style={{position: 'absolute', left: 112, top: 414, ...big, fontSize: 330, lineHeight: 0.98}}>
				<Rise p={tween(frame, 0, 8, 0, 1, ease.enter)}>Isto</Rise>
				<div style={{display: 'flex', gap: 46, alignItems: 'baseline'}}>
					<span style={{display: 'inline-block', color: C.accent, transform: `scale(${no})`, transformOrigin: '0 100%'}}>não</span>
					<Rise p={tween(frame, at('nao') + 3, 7, 0, 1, ease.enter)}>é</Rise>
				</div>
				<div style={{position: 'relative', display: 'inline-block'}}>
					<Rise p={tween(frame, at('edicao') - 2, 8, 0, 1, ease.enter)}>edição</Rise>
					<div style={{position: 'absolute', left: -14, right: -14, top: '46%', height: 26, background: C.accent, transformOrigin: '0 50%', transform: `scaleX(${strike}) rotate(-3deg)`}} />
				</div>
			</div>
		</AbsoluteFill>
	);
};

const SNIPPET = `const {frame, at} =
  useScene('codigo');
const p = tween(frame,
  at('codigo'), 12, 0, 1);
return <Rise p={p} />;`;

/** Cena 2: corte seco para o limão. A janela digita o código que desenha esta mesma cena. */
const Codigo: React.FC = () => {
	const {frame, len, at} = useScene('codigo');
	return (
		<AbsoluteFill style={{background: C.lime, color: C.bg}}>
			<div data-decor>
				<Marquee items={['useCurrentFrame()', 'spring()', 'interpolate()', 'tween()']} variant="outline" fill={C.lime} color={C.bg} y={1560} rotate={-6} fontSize={150} period={110} />
			</div>
			<Counter color={C.bg} id="codigo" />
			<div style={{position: 'absolute', left: 112, top: 420, ...big, fontSize: 290}}>
				<Rise p={tween(frame, 1, 7, 0, 1, ease.enter)}>É</Rise>
				<Rise p={tween(frame, at('codigo') - 2, 8, 0, 1, easeX.emphasized)}>código.</Rise>
			</div>
			<div style={{position: 'absolute', left: 108, top: 1010, width: 864}}>
				<CodeWindow code={SNIPPET} title="Codigo.tsx" at={at('codigo') + 4} out={len - 2} cps={80} fontSize={44} width={864} />
			</div>
		</AbsoluteFill>
	);
};

/** Cena 3: o contador vira herói. A grade acende uma célula por frame: dá para contar. */
const Frame: React.FC = () => {
	const {frame, len, at} = useScene('frame');
	const abs = frame + Math.round(sceneOf('frame').start * timeline.fps);
	const durationInFrames = TOTAL;
	const cols = 9;
	const rows = 16;
	const cell = W / cols;
	const lit = Math.max(0, frame - 2) * 1.6;
	const shown = abs;
	return (
		<AbsoluteFill style={{background: C.second, color: C.ink}}>
			<svg width={W} height={H} data-decor>
				{Array.from({length: cols * rows}, (_, i) => {
					const on = i < lit;
					const head = Math.floor(lit) === i;
					return on ? <rect key={i} x={(i % cols) * cell + 10} y={Math.floor(i / cols) * cell + 10} width={cell - 20} height={cell - 20} fill={C.ink} opacity={head ? 0.5 : 0.13} /> : null;
				})}
			</svg>
			<div style={{position: 'absolute', left: 112, top: 500, ...big, fontSize: 390, fontVariantNumeric: 'tabular-nums'}}>
				<Rise p={tween(frame, 1, 8, 0, 1, ease.enter)}>{pad4(shown)}</Rise>
			</div>
			<div style={{position: 'absolute', left: 108, top: 950, fontFamily: MONO, fontSize: 40, fontWeight: 700}}>
				<Rise p={tween(frame, 8, 8, 0, 1, ease.sharp)}>de {pad4(durationInFrames)} frames</Rise>
			</div>
			<div style={{position: 'absolute', left: 112, top: 1060, ...big, fontSize: 150}}>
				<Rise p={Math.min(tween(frame, at('frame') - 8, 8, 0, 1, ease.enter), 1 - tween(frame, len - 6, 6, 0, 1, ease.exit))}>Cada frame,</Rise>
				<Rise p={Math.min(tween(frame, at('calculado') - 2, 8, 0, 1, ease.enter), 1 - tween(frame, len - 6, 6, 0, 1, ease.exit))}>
					<span style={{color: C.lime}}>calculado.</span>
				</Rise>
			</div>
		</AbsoluteFill>
	);
};

const SHAPES = [circlePath(540, 740, 270), starPath(540, 740, 330, 5, 0.5), blobPath(540, 740, 290, 'k'), roundedRectPath(305, 505, 470, 470, 60), starPath(540, 740, 330, 12, 0.72), circlePath(540, 740, 270)];

/** Cena 4: um corte por batida da trilha. Cada batida troca as duas cores e a forma muda de espécie. */
const Batida: React.FC = () => {
	const {frame, len, at, fps} = useScene('batida');
	const start = sceneOf('batida').start;
	const t = start + frame / fps;
	const beats = BEATS.filter((b) => b >= start - 0.01 && b < sceneOf('batida').end - 0.02);
	const k = Math.max(0, beats.filter((b) => b <= t + 0.004).length - 1);
	const since = (t - beats[k]) * fps;
	const pairs: Array<[string, string, string]> = [
		[C.accent, C.bg, C.ink],
		[C.ink, C.second, C.accent],
		[C.pink, C.bg, C.lime],
		[C.bg, C.lime, C.pink],
		[C.second, C.ink, C.accent],
		[C.lime, C.bg, C.second],
	];
	// Só troca de pôster depois que a frase foi dita: antes disso a batida só pulsa a forma.
	const free = frame >= at('b1');
	const n = free ? 1 + beats.filter((b) => b <= t + 0.004 && b >= start + at('b1') / fps - 0.01).length : 0;
	const [bg, fg, dot] = pairs[n % pairs.length];
	const hit = squash(keys(since, [0, 2, 9], [-0.16, 0.1, 0], [ease.sharp, ease.settle]));
	const morph = n % (SHAPES.length - 1) + tween(since, 0, 7, -1, 0, ease.move);
	return (
		<AbsoluteFill style={{background: bg, color: fg}}>
			<Counter color={fg} id="batida" />
			<div data-decor style={{position: 'absolute', right: 96, top: 1440, ...big, fontSize: 330, color: dot, opacity: free ? 1 : 0}}>
				{String(n).padStart(2, '0')}
			</div>
			<svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
				<g transform={`translate(540 740) scale(${hit.sx} ${hit.sy}) rotate(${n * 18}) translate(-540 -740)`}>
					<path d={morphPath(SHAPES, Math.max(0, morph))} fill={fg} />
				</g>
				<circle cx={540} cy={740} r={34 + 10 * hit.sy} fill={dot} />
			</svg>
			<div style={{position: 'absolute', left: 112, top: 1110, ...big, fontSize: 160}}>
				<Rise p={Math.min(tween(frame, 0, 7, 0, 1, ease.enter), 1 - tween(frame, len - 5, 5, 0, 1, ease.exit))}>Cada corte,</Rise>
				<Rise p={Math.min(tween(frame, at('batida') - 2, 7, 0, 1, ease.enter), 1 - tween(frame, len - 5, 5, 0, 1, ease.exit))}>na batida.</Rise>
			</div>
		</AbsoluteFill>
	);
};

/** Cena 5: papel claro. As três palavras empilham à esquerda; os sólidos ficam à direita, no Shapes3D. */
const Tresd: React.FC = () => {
	const {frame, len, at} = useScene('tresd');
	const out = tween(frame, len - 7, 7, 0, 1, ease.exit);
	const row = (c: 'cor' | 'forma' | 'tres') => Math.min(tween(frame, at(c) - 2, 8, 0, 1, ease.enter), 1 - out);
	const push = tween(frame, at('tres'), 22, 0, 1, ease.move);
	return (
		<AbsoluteFill style={{background: C.ink, color: C.bg}}>
			<Counter color={C.bg} id="tresd" />
			<div style={{position: 'absolute', left: 112, top: 420, ...big, fontSize: 210}}>
				<Rise p={row('cor')}>
					<span style={{color: C.second}}>Cor,</span>
				</Rise>
				<Rise p={row('forma')}>forma</Rise>
				<Rise p={row('tres')} style={{fontSize: 210 + push * 90}}>
					3D
				</Rise>
			</div>
			<Shapes3D />
		</AbsoluteFill>
	);
};

// Medidas reais dos gates da skill durante a produção do outro vídeo desta rodada: o valor reprovado e o valor depois do conserto.
const CHECKS: Array<[string, string, string]> = [
	['letra de', '9 px', '58 px'],
	['pico do áudio', '-0.1 dBTP', '-3.3 dBTP'],
	['textos sobrepostos', '2', '0'],
];

/** Cena 6: o revisor. Três reprovações reais são consertadas (o valor muda) e só então viram PASS; o carimbo cai no tempo do SFX. */
const Revisor: React.FC = () => {
	const {frame, len, at} = useScene('revisor');
	// O estouro de cores cobre o fim desta cena: tudo sai antes de ele começar.
	const out = tween(frame, len - BURST - 7, 6, 0, 1, ease.exit);
	const stamp = pop(frame, 30, at('pass') - 1, springs.snappy) * (1 - out);
	if (frame >= len - BURST) return <AbsoluteFill style={{background: C.bg}} />;
	return (
		<AbsoluteFill style={{background: C.bg, color: C.ink}}>
			<Counter color={C.muted} id="revisor" />
			<div style={{position: 'absolute', left: 108, top: 470, width: 864, fontFamily: MONO, fontSize: 42, fontWeight: 700, lineHeight: 1.2}}>
				{CHECKS.map(([what, bad, good], i) => {
					const fixed = frame >= at('erro') + 6 + i * 7;
					return (
						<Rise key={what} p={Math.min(tween(frame, 3 + i * 4, 7, 0, 1, ease.sharp), 1 - out)} style={{marginBottom: 30}}>
							<span style={{color: fixed ? C.lime : C.accent}}>{fixed ? 'PASS' : 'FAIL'}</span>
							<span>
								{' '}
								{what} <span style={{color: fixed ? C.lime : C.accent}}>{fixed ? good : bad}</span>
							</span>
						</Rise>
					);
				})}
			</div>
			<div style={{position: 'absolute', left: 520, top: 690, transform: `rotate(-9deg) scale(${stamp})`, transformOrigin: '50% 50%', border: `14px solid ${C.lime}`, padding: '8px 36px 0', ...big, fontSize: 180, color: C.lime}}>
				pass
			</div>
			<div style={{position: 'absolute', left: 112, top: 968, ...big, fontSize: 146}}>
				<Rise p={Math.min(tween(frame, 2, 8, 0, 1, ease.enter), 1 - out)}>E um revisor</Rise>
				<Rise p={Math.min(tween(frame, at('revisor') + 8, 8, 0, 1, ease.enter), 1 - out)}>que não deixa</Rise>
				<Rise p={Math.min(tween(frame, at('erro') - 12, 8, 0, 1, ease.enter), 1 - out)}>
					passar <span style={{color: C.accent}}>erro.</span>
				</Rise>
			</div>
		</AbsoluteFill>
	);
};

/** Cena 7: as cinco cores estouram em anéis e fecham no preto; o nome monta no tempo da voz. */
const Fecho: React.FC = () => {
	const {frame, at} = useScene('fecho');
	// Do mais claro ao mais escuro: a luminância só desce, então o estouro de cor não vira pisca-pisca (o qa.py conta flashes).
	const row = (c: 'nome' | 'motion' | 'design') => tween(frame, at(c) - 2, 8, 0, 1, easeX.emphasized);
	const tag = (c: 'prompt' | 'video') => tween(frame, at(c) - 2, 7, 0, 1, ease.sharp);
	return (
		<AbsoluteFill style={{background: C.bg, color: C.ink}}>
			<Counter color={C.muted} id="fecho" />
			<div data-decor>
				<Marquee items={['um prompt', 'um vídeo', 'zero timeline']} variant="outline" fill={C.bg} color={C.muted} y={1650} rotate={-5} fontSize={170} period={120} at={at('design')} />
			</div>
			<div style={{position: 'absolute', left: 112, top: 440, ...big, fontSize: 236}}>
				<Rise p={row('nome')}>Extreme</Rise>
				<Rise p={row('motion')}>Motion</Rise>
				<Rise p={row('design')}>
					<span style={{color: C.accent}}>Design</span>
				</Rise>
			</div>
			<div style={{position: 'absolute', left: 108, top: 1182, display: 'flex', gap: 22, ...big, fontSize: 76, color: C.bg}}>
				{(['prompt', 'video'] as const).map((c, i) => (
					<span key={c} style={{display: 'inline-block', background: i ? C.pink : C.lime, padding: '14px 26px 4px', clipPath: `inset(0 ${(1 - tag(c)) * 100}% 0 0)`}}>
						{i ? 'um vídeo.' : 'um prompt.'}
					</span>
				))}
			</div>
			<svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
				<path d="M 108 1158 H 972" stroke={C.line} strokeWidth={4} fill="none" {...trim(tween(frame, at('design') + 6, 14, 0, 1, ease.enter))} />
			</svg>
			<div style={{position: 'absolute', left: 108, top: 1296, fontFamily: MONO, fontSize: 34, fontWeight: 700, lineHeight: 1.25, color: C.ink}}>
				<Rise p={tween(frame, at('assina') - 2, 9, 0, 1, ease.enter)}>
					<span style={{fontFamily: FONT, color: C.muted}}>Instale pelo GitHub</span>
				</Rise>
				<Rise p={tween(frame, at('assina') + 1, 9, 0, 1, ease.enter)}>dev-isaacmello/</Rise>
				<Rise p={tween(frame, at('assina') + 3, 9, 0, 1, ease.enter)}>extreme-motion-design</Rise>
			</div>
		</AbsoluteFill>
	);
};

/** Passagem para o fecho: anéis das cores, do mais claro ao mais escuro. A luminância só desce, então não vira pisca-pisca (o qa.py conta flashes). */
const Burst: React.FC = () => {
	const frame = useCurrentFrame();
	const rings = [C.lime, C.pink, C.accent, C.second, C.bg];
	return (
		<>
			{rings.map((c, i) => (
				<IrisReveal key={c} progress={tween(frame, i * 2, 9, 0, 1, ease.move)} cy="46%">
					<AbsoluteFill style={{background: c}} />
				</IrisReveal>
			))}
		</>
	);
};

export const Reel: React.FC = () => (
	<AbsoluteFill style={{background: C.bg, fontFamily: FONT}}>
		<Scene id="nao">
			<Nao />
		</Scene>
		<Scene id="codigo">
			<Codigo />
		</Scene>
		<Scene id="frame">
			<Frame />
		</Scene>
		<Scene id="batida">
			<Batida />
		</Scene>
		<Scene id="tresd">
			<Tresd />
		</Scene>
		<Scene id="revisor">
			<Revisor />
		</Scene>
		<Sequence from={Math.round(sceneOf('fecho').start * timeline.fps) - BURST} durationInFrames={BURST} name="estouro">
			<Burst />
		</Sequence>
		<Scene id="fecho">
			<Fecho />
		</Scene>
		<Grain opacity={0.05} vignette={0} />
		{timeline.audio ? <Audio src={staticFile(timeline.audio)} /> : null}
		<Probe />
	</AbsoluteFill>
);
