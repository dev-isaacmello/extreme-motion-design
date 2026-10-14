import React from 'react';
import {AbsoluteFill} from 'remotion';
import {useFormat} from '../lib/format';
import {dur, ease, pop, springs} from '../lib/motion';
import {C, FONT, type} from '../theme';
import {BlockTiming, Rise, alpha, trim, useBlock} from './shared';

type Pt = {x: number; y: number};

/**
 * Rótulo com linha guia: o ponto marca o alvo, a linha se desenha até o cotovelo e segue sob o texto.
 * `from` é o alvo e `to` o cotovelo, em px do quadro. O texto abre para o lado oposto ao alvo.
 */
export const Callout: React.FC<
	BlockTiming & {
		from: Pt;
		to: Pt;
		label: string;
		detail?: string;
		/** Comprimento do trecho horizontal em px reais. */
		width?: number;
		color?: string;
		accent?: string;
	}
> = ({from, to, label, detail, width, color = C.ink, accent = C.accent, at = 0, out}) => {
	const {u} = useFormat();
	const {frame, rise, exit} = useBlock(at, out);
	const lw = width ?? 380 * u;
	const dir = to.x >= from.x ? 1 : -1;
	const dot = Math.min(pop(frame, 30, 0, springs.snappy), 1.3) * (1 - exit);
	const pulse = rise(2, dur.slow, ease.settle);
	return (
		<AbsoluteFill style={{pointerEvents: 'none', fontFamily: FONT}}>
			<svg width="100%" height="100%" style={{position: 'absolute', inset: 0, overflow: 'visible'}}>
				<path
					d={`M ${from.x} ${from.y} L ${to.x} ${to.y} L ${to.x + dir * lw} ${to.y}`}
					fill="none"
					stroke={color}
					strokeWidth={3 * u}
					strokeLinejoin="round"
					{...trim(rise(4, 18, ease.move))}
				/>
				<circle cx={from.x} cy={from.y} r={(12 + 22 * pulse) * u} fill="none" stroke={alpha(accent, 0.5 * (1 - pulse))} strokeWidth={3 * u} />
				<circle cx={from.x} cy={from.y} r={11 * u * dot} fill={accent} stroke={C.bg} strokeWidth={4 * u * dot} />
			</svg>
			<div style={{position: 'absolute', left: dir > 0 ? to.x : to.x - lw, top: to.y, width: lw, textAlign: dir > 0 ? 'left' : 'right'}}>
				<div
					style={{
						position: 'absolute',
						left: 0,
						right: 0,
						bottom: 14 * u,
						fontSize: type.body * 0.9 * u,
						fontWeight: 700,
						lineHeight: 1.15,
						letterSpacing: '-0.02em',
						color: C.ink,
					}}
				>
					<Rise p={rise(16, dur.base)}>{label}</Rise>
				</div>
				{detail ? (
					<div style={{position: 'absolute', left: 0, right: 0, top: 14 * u, fontSize: type.label * u, fontWeight: 500, lineHeight: 1.3, color: C.muted}}>
						<Rise p={rise(19, dur.base)}>{detail}</Rise>
					</div>
				) : null}
			</div>
		</AbsoluteFill>
	);
};
