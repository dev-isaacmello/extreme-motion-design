import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import timeline from '../../public/timeline.json';
import narration from '../../public/audio/narration.words.json';
import {Camera, Layer} from '../components/Camera';
import {BoilFilter, Grain} from '../components/Fx';
import {KineticWords, Word} from '../components/KineticWords';
import {morphPath} from '../components/Morph';
import {blobPath, circlePath, starPath} from '../lib/shapes';
import {twoBoneIK} from '../lib/rig';
import {clamp, ease, keys, loopPhase, springs, stepped, tween, wiggle} from '../lib/motion';

// Paleta: tinta escura, papel quente e um único acento. Sem gradiente roxo, sem glow genérico.
const C = {bg: '#0F1114', paper: '#F3EFE6', accent: '#FFB547', cool: '#6E8BFF', line: '#2B2F36'};
const FONT = 'Inter, "Helvetica Neue", Arial, sans-serif';

const scene = (id: string) => timeline.scenes.find((s) => s.id === id)!;

/** Entrada e saída de cena: whip curto com blur, casado nos dois lados do corte. */
const Whip: React.FC<{len: number; children: React.ReactNode}> = ({len, children}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const inP = spring({frame, fps, config: springs.smooth, durationInFrames: 10});
	const outP = interpolate(frame, [len - 8, len], [0, 1], {...clamp, easing: ease.exit});
	const x = (1 - inP) * 140 - outP * 140;
	const blur = (1 - inP) * 14 + outP * 14;
	return <AbsoluteFill style={{transform: `translateX(${x}px)`, filter: `blur(${blur}px)`}}>{children}</AbsoluteFill>;
};

const Kinetic: React.FC<{len: number}> = ({len}) => {
	const frame = useCurrentFrame();
	// Push-in lento (zoom in) com deriva de câmera na mão.
	const zoom = tween(frame, 0, len, 1, 1.12, ease.move);
	const dx = wiggle('cam-x', frame, 0.03, 6);
	const dy = wiggle('cam-y', frame, 0.03, 4);
	const draw = tween(frame, 6, 40, 1, 0, ease.enter);
	return (
		<Whip len={len}>
			<Camera zoom={zoom} x={dx} y={dy}>
				<Layer depth={3}>
					<svg width="100%" height="100%" viewBox="0 0 1920 1080">
						{Array.from({length: 7}, (_, i) => (
							<circle key={i} cx={260 + i * 240} cy={540 + Math.sin(i * 1.7) * 260} r={70 + (i % 3) * 40} fill={C.line} opacity={0.55} />
						))}
					</svg>
				</Layer>
				<Layer depth={1.6}>
					<svg width="100%" height="100%" viewBox="0 0 1920 1080">
						<path
							d="M 140 820 C 520 640, 760 980, 1120 760 S 1700 640, 1800 300"
							fill="none"
							stroke={C.accent}
							strokeWidth={6}
							strokeLinecap="round"
							pathLength={1}
							strokeDasharray={1}
							strokeDashoffset={draw}
						/>
					</svg>
				</Layer>
			</Camera>
		</Whip>
	);
};

const MorphRig: React.FC<{len: number}> = ({len}) => {
	const frame = useCurrentFrame();
	const shapes = [circlePath(560, 540, 210), starPath(560, 540, 250), blobPath(560, 540, 220, 'b1')];
	// Keyframes com hold: segura a forma, troca com ease.move.
	const progress = keys(frame, [0, 12, 30, 48, 66], [0, 0, 1, 1, 2], [ease.move, ease.move, ease.move, ease.move]);
	const fill = progress < 1 ? C.paper : progress < 2 ? C.accent : C.cool;
	// Rig: alvo percorre um oito; animado em twos para o look cel.
	const f2 = stepped(frame, 2);
	const a = (f2 / len) * Math.PI * 2;
	const target = {x: 1360 + Math.cos(a) * 170, y: 560 + Math.sin(2 * a) * 120};
	const root = {x: 1360, y: 260};
	const ik = twoBoneIK(root, target, 210, 200, -1);
	return (
		<Whip len={len}>
			<svg width="100%" height="100%" viewBox="0 0 1920 1080">
				<defs>
					<BoilFilter id="boil" hold={2} scale={4} />
				</defs>
				<path d={morphPath(shapes, progress)} fill={fill} />
				<g filter="url(#boil)" stroke={C.paper} strokeLinecap="round" fill="none">
					<line x1={root.x} y1={root.y} x2={ik.elbow.x} y2={ik.elbow.y} strokeWidth={34} />
					<line x1={ik.elbow.x} y1={ik.elbow.y} x2={ik.hand.x} y2={ik.hand.y} strokeWidth={26} />
					<circle cx={root.x} cy={root.y} r={26} fill={C.bg} strokeWidth={8} />
					<circle cx={ik.elbow.x} cy={ik.elbow.y} r={20} fill={C.bg} strokeWidth={8} />
					<circle cx={ik.hand.x} cy={ik.hand.y} r={30} fill={C.accent} stroke="none" />
				</g>
			</svg>
		</Whip>
	);
};

const LoopUI: React.FC<{len: number}> = ({len}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	// Zoom out que revela a composição e assenta sem overshoot.
	const zoom = tween(frame, 0, Math.min(len, 40), 1.18, 1, ease.settle);
	// Loop perfeito: período divide a duração da cena; o frame `period` repete o 0.
	const period = 45;
	const ph = loopPhase(frame, period);
	// Microinteração: cursor chega em arco, clica, toggle liga com spring.
	const clickAt = 22;
	const cx = interpolate(frame, [0, clickAt], [1700, 1395], {...clamp, easing: ease.move});
	const cy = interpolate(frame, [0, clickAt], [900, 556], {...clamp, easing: ease.move}) - Math.sin(Math.min(frame / clickAt, 1) * Math.PI) * 60;
	const press = interpolate(frame, [clickAt - 2, clickAt, clickAt + 4], [1, 0.9, 1], clamp);
	const on = spring({frame: frame - clickAt, fps, config: springs.snappy});
	const ripple = interpolate(frame, [clickAt, clickAt + 14], [0, 1], clamp);
	return (
		<Whip len={len}>
			<Camera zoom={zoom}>
				<Layer>
					<svg width="100%" height="100%" viewBox="0 0 1920 1080">
						<g transform="translate(600 540)">
							<circle r={190} fill="none" stroke={C.line} strokeWidth={3} />
							{Array.from({length: 6}, (_, i) => {
								const ang = (ph + i / 6) * Math.PI * 2;
								return <circle key={i} cx={Math.cos(ang) * 190} cy={Math.sin(ang) * 190} r={18 + 8 * Math.sin(ph * Math.PI * 2 + i)} fill={i === 0 ? C.accent : C.paper} />;
							})}
						</g>
						<g transform={`translate(1400 560) scale(${press})`}>
							<rect x={-110} y={-56} width={220} height={112} rx={56} fill={interpolate(on, [0, 1], [0, 1]) > 0.5 ? C.accent : C.line} />
							<circle cx={interpolate(on, [0, 1], [-54, 54])} cy={0} r={44} fill={C.paper} />
						</g>
						<circle cx={1395} cy={556} r={40 + ripple * 120} fill="none" stroke={C.paper} strokeWidth={4} opacity={(1 - ripple) * (frame >= clickAt ? 0.6 : 0)} />
						<path d="M0,0 L0,46 L12,34 L22,56 L30,52 L20,31 L36,31 Z" transform={`translate(${cx} ${cy})`} fill={C.paper} stroke={C.bg} strokeWidth={3} />
					</svg>
				</Layer>
			</Camera>
		</Whip>
	);
};

export const Showcase: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const words = narration.words as Word[];
	const s1 = scene('kinetic');
	const s2 = scene('morph-rig');
	const s3 = scene('loop-ui');
	const f = (s: number) => Math.round(s * fps);
	const hero = frame < f(s2.start);
	return (
		<AbsoluteFill style={{background: C.bg, fontFamily: FONT}}>
			<Sequence from={f(s1.start)} durationInFrames={f(s1.end - s1.start)}>
				<Kinetic len={f(s1.end - s1.start)} />
			</Sequence>
			<Sequence from={f(s2.start)} durationInFrames={f(s2.end - s2.start)}>
				<MorphRig len={f(s2.end - s2.start)} />
			</Sequence>
			<Sequence from={f(s3.start)} durationInFrames={f(s3.end - s3.start)}>
				<LoopUI len={f(s3.end - s3.start)} />
			</Sequence>
			<KineticWords
				words={words}
				offsetSec={timeline.narration.start}
				fontSize={hero ? 132 : 64}
				top={hero ? '47%' : '86%'}
				maxWords={hero ? 3 : 6}
				color={C.paper}
				accent={C.accent}
			/>
			<Grain />
			{timeline.audio ? <Audio src={staticFile(timeline.audio)} /> : null}
		</AbsoluteFill>
	);
};
