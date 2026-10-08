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
