import React from 'react';
import {useFormat} from '../lib/format';
import {dur, ease, easeX, ticker} from '../lib/motion';
import {C, FONT, type} from '../theme';
import {BlockTiming, Rise, trim, useBlock} from './shared';

/** Anel de progresso: o trilho se desenha, o arco avança até o valor e o número conta no centro. */
export const Donut: React.FC<
	BlockTiming & {
		value: number;
		max?: number;
		suffix?: string;
		label?: string;
		/** Diâmetro em px do quadro de 1080 (multiplicado por u). */
		size?: number;
		thickness?: number;
		color?: string;
	}
> = ({value, max = 100, suffix = '%', label, size = 440, thickness, color = C.accent, at = 0, out}) => {
	const {u} = useFormat();
	const {frame, rise} = useBlock(at, out);
	const s = size * u;
	const t = (thickness ?? size * 0.085) * u;
	const r = (s - t) / 2;
	const frac = Math.min(1, Math.max(0, value / max));
	const arc = rise(8, 34, easeX.emphasized) * frac;
	return (
		<div style={{position: 'relative', width: s, height: s, fontFamily: FONT}}>
			<svg width={s} height={s} viewBox={`0 0 ${s} ${s}`} style={{position: 'absolute', inset: 0}}>
				<g transform={`rotate(-90 ${s / 2} ${s / 2})`}>
					<circle cx={s / 2} cy={s / 2} r={r} fill="none" stroke={C.line} strokeWidth={t} {...trim(rise(0, dur.slow, ease.settle))} />
					{arc > 0.002 ? (
						<circle
							cx={s / 2}
							cy={s / 2}
							r={r}
							fill="none"
							stroke={color}
							strokeWidth={t}
							strokeLinecap="round"
							pathLength={1}
							strokeDasharray={`${arc} 2`}
						/>
					) : null}
				</g>
			</svg>
			<div
				style={{
					position: 'absolute',
					inset: 0,
					display: 'flex',
					flexDirection: 'column',
					alignItems: 'center',
					justifyContent: 'center',
					textAlign: 'center',
				}}
			>
				<Rise p={rise(6, dur.slow)}>
					<span
						style={{
							fontSize: s * 0.25,
							fontWeight: 800,
							lineHeight: 1,
							letterSpacing: '-0.04em',
							fontVariantNumeric: 'tabular-nums',
							color: C.ink,
						}}
					>
						{ticker(frame, 8, 34, 0, value).toLocaleString('pt-BR')}
						<span style={{fontSize: '0.5em', fontWeight: 700, marginLeft: '0.06em', color: C.muted}}>{suffix}</span>
					</span>
				</Rise>
				{label ? (
					<div style={{marginTop: s * 0.03, maxWidth: r * 1.5, fontSize: type.label * u, fontWeight: 500, lineHeight: 1.25, color: C.muted}}>
						<Rise p={rise(12, dur.base)}>{label}</Rise>
					</div>
				) : null}
			</div>
		</div>
	);
};
