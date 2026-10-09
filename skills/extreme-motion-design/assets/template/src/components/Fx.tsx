import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';

/**
 * Line boil de animação cel: o traço "ferve" porque o ruído muda a cada `hold` frames.
 * Use dentro de <defs> e aplique com filter="url(#id)" num <g>.
 */
export const BoilFilter: React.FC<{id: string; hold?: number; scale?: number; freq?: number}> = ({
	id,
	hold = 2,
	scale = 3.5,
	freq = 0.03,
}) => {
	const frame = useCurrentFrame();
	return (
		<filter id={id} x="-10%" y="-10%" width="120%" height="120%">
			<feTurbulence type="fractalNoise" baseFrequency={freq} numOctaves={2} seed={Math.floor(frame / hold) % 97} result="n" />
			<feDisplacementMap in="SourceGraphic" in2="n" scale={scale} xChannelSelector="R" yChannelSelector="G" />
		</filter>
	);
};

/** Grão de filme e vinheta por cima de tudo: integra elementos e quebra o banding. */
export const Grain: React.FC<{opacity?: number; vignette?: number}> = ({opacity = 0.06, vignette = 0.42}) => {
	const frame = useCurrentFrame();
	return (
		<AbsoluteFill style={{pointerEvents: 'none'}}>
			<svg width="100%" height="100%" style={{position: 'absolute', inset: 0, mixBlendMode: 'overlay', opacity}}>
				<filter id="grain-f">
					<feTurbulence type="fractalNoise" baseFrequency={0.85} numOctaves={1} seed={frame % 59} stitchTiles="stitch" />
					<feColorMatrix type="saturate" values="0" />
				</filter>
				<rect width="100%" height="100%" filter="url(#grain-f)" />
			</svg>
			<AbsoluteFill
				style={{background: `radial-gradient(ellipse at center, transparent 52%, rgba(0,0,0,${vignette}) 100%)`}}
			/>
		</AbsoluteFill>
	);
};

/** Eco (trails): cópias atrasadas do mesmo desenho. `render` recebe o frame atrasado de cada cópia. */
export const Echo: React.FC<{copies?: number; lag?: number; render: (frame: number, i: number) => React.ReactNode}> = ({
	copies = 4,
	lag = 2,
	render,
}) => {
	const frame = useCurrentFrame();
	return (
		<>
			{Array.from({length: copies}, (_, k) => copies - 1 - k).map((i) => (
				<AbsoluteFill key={i} style={{opacity: i === 0 ? 1 : 0.5 * (1 - i / copies)}}>
					{render(frame - i * lag, i)}
				</AbsoluteFill>
			))}
		</>
	);
};

/** Transição por forma: círculo que abre (progress 0 -> 1) revelando os filhos. Corte casado por cor chapada. */
export const IrisReveal: React.FC<{progress: number; cx?: string; cy?: string; children: React.ReactNode}> = ({
	progress,
	cx = '50%',
	cy = '50%',
	children,
}) => (
	<AbsoluteFill style={{clipPath: `circle(${Math.max(0, progress) * 142}% at ${cx} ${cy})`}}>{children}</AbsoluteFill>
);

/** Revelação por máscara de linha (baseline reveal): o conteúdo sobe de trás de uma borda reta. */
export const MaskReveal: React.FC<{progress: number; children: React.ReactNode; style?: React.CSSProperties}> = ({
	progress,
	children,
	style,
}) => (
	<span style={{display: 'inline-block', overflow: 'hidden', verticalAlign: 'bottom', ...style}}>
		<span style={{display: 'inline-block', transform: `translateY(${(1 - Math.min(1, Math.max(0, progress))) * 105}%)`}}>
			{children}
		</span>
	</span>
);

/** Varredura de luz (shine) sobre os filhos: uma passada, progress 0 -> 1. Use uma vez, no logo ou no dado principal. */
export const Shine: React.FC<{progress: number; angle?: number; width?: number; children: React.ReactNode}> = ({
	progress,
	angle = 24,
	width = 20,
	children,
}) => {
	const p = -width + progress * (100 + 2 * width);
	const band = `linear-gradient(${90 + angle}deg, transparent ${p - width}%, rgba(255,255,255,0.75) ${p}%, transparent ${p + width}%)`;
	return (
		<span style={{position: 'relative', display: 'inline-block'}}>
			{children}
			<span
				aria-hidden
				style={{
					position: 'absolute',
					inset: 0,
					backgroundImage: band,
					mixBlendMode: 'overlay',
					pointerEvents: 'none',
				}}
			/>
		</span>
	);
};

/** Filtro gooey para transição líquida: aplique com filter="url(#id)" no grupo de formas que se fundem. */
export const GooeyFilter: React.FC<{id: string; blur?: number}> = ({id, blur = 14}) => (
	<filter id={id}>
		<feGaussianBlur in="SourceGraphic" stdDeviation={blur} result="b" />
		<feColorMatrix in="b" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 22 -9" />
	</filter>
);
