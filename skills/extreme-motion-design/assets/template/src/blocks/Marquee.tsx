import React from 'react';
import {AbsoluteFill} from 'remotion';
import {useFormat} from '../lib/format';
import {dur, ease, loopPhase} from '../lib/motion';
import {C, FONT, type} from '../theme';
import {BlockTiming, mix, useBlock} from './shared';

/**
 * Faixa de texto em loop sem emenda. A fita são duas metades iguais e anda uma repetição do texto a cada
 * `period` frames: o frame `period` é idêntico ao 0, então fecha loop quando o período divide a cena.
 * É ornamento (data-decor): sangra do quadro e não entra na medição de área segura.
 */
export const Marquee: React.FC<
	BlockTiming & {
		items: string[];
		/** outline: contorno discreto para fundo. solid: texto cheio. band: faixa no acento, para transição. */
		variant?: 'outline' | 'solid' | 'band';
		/** Cor de dentro das letras no outline. Tem de ser a do fundo atrás da faixa. */
		fill?: string;
		/** Frames para o texto andar uma repetição inteira. */
		period?: number;
		direction?: 1 | -1;
		/** Centro da faixa em px a partir do topo. Padrão: meio do quadro. */
		y?: number;
		rotate?: number;
		fontSize?: number;
		color?: string;
		accent?: string;
	}
> = ({items, variant = 'outline', fill = C.bg, period = 150, direction = 1, y, rotate = 0, fontSize = type.hero, color, accent = C.accent, at = 0, out}) => {
	const {u, width, height} = useFormat();
	const {frame, rise, k} = useBlock(at, out);
	const size = fontSize * u;
	const band = variant === 'band';
	const ink = color ?? (band ? C.bg : variant === 'solid' ? C.ink : mix(C.ink, C.bg, 0.3));
	// Estimativa folgada da largura de uma repetição, só para decidir quantas cabem numa metade.
	const unit = items.reduce((n, t) => n + t.length * 0.5 + 1.2, 0) * size;
	const reps = Math.max(1, Math.ceil((width * 1.3) / unit));
	const phase = loopPhase(frame * k, period);
	const shift = ((direction > 0 ? phase : 1 - phase) / reps) * 50;
	const open = rise(0, dur.base, ease.settle);
	const half = (h: number) => (
		<div key={h} style={{display: 'flex', flexShrink: 0}}>
			{Array.from({length: reps}, (_, r) =>
				items.map((t, i) => (
					<div key={`${r}-${i}`} style={{display: 'flex', alignItems: 'center', flexShrink: 0}}>
						{/* No outline o preenchimento cobre o traço de dentro: fonte variável tem contornos sobrepostos que apareceriam. */}
						<span style={variant === 'outline' ? {color: fill, WebkitTextStroke: `${4 * u}px ${ink}`, paintOrder: 'stroke fill'} : {color: ink}}>{t}</span>
						<span style={{width: size * 0.16, height: size * 0.16, margin: `0 ${size * 0.4}px`, borderRadius: size, background: variant === 'solid' ? accent : ink, flexShrink: 0}} />
					</div>
				)),
			)}
		</div>
	);
	return (
		<AbsoluteFill data-decor style={{pointerEvents: 'none', overflow: 'hidden'}}>
			<div
				style={{
					position: 'absolute',
					left: -width * 0.1,
					width: width * 1.2,
					top: y ?? height / 2,
					transform: `translateY(-50%) rotate(${rotate}deg)`,
					clipPath: `inset(${(1 - open) * 50}% 0)`,
					background: band ? accent : 'transparent',
					padding: band ? `${size * 0.18}px 0` : 0,
					fontFamily: FONT,
					fontSize: size,
					fontWeight: 800,
					lineHeight: 1.1,
					letterSpacing: '-0.035em',
					whiteSpace: 'nowrap',
				}}
			>
				<div style={{display: 'flex', width: 'max-content', transform: `translateX(${-shift}%)`}}>{[0, 1].map(half)}</div>
			</div>
		</AbsoluteFill>
	);
};
