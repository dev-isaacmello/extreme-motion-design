import React, {useId, useMemo} from 'react';
import {getLength, getPointAtLength} from '@remotion/paths';
import {useFormat} from '../lib/format';
import {dur, ease, pop, springs} from '../lib/motion';
import {C, FONT, type} from '../theme';
import {BlockTiming, Rise, trim, useBlock} from './shared';

type Pt = {x: number; y: number};

// Cúbica monótona (Fritsch-Carlson): suaviza sem passar do valor real entre dois pontos.
const smoothPath = (pts: Pt[]) => {
	const n = pts.length;
	if (n < 3) return pts.map((p, i) => `${i ? 'L' : 'M'} ${p.x} ${p.y}`).join(' ');
	const d = pts.slice(1).map((p, i) => (p.y - pts[i].y) / (p.x - pts[i].x));
	const t = pts.map((_, i) => (i === 0 ? d[0] : i === n - 1 ? d[n - 2] : d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2));
	for (let i = 0; i < n - 1; i++) {
		if (d[i] === 0) {
			t[i] = 0;
			t[i + 1] = 0;
			continue;
		}
		const a = t[i] / d[i];
		const b = t[i + 1] / d[i];
		const s = a * a + b * b;
		if (s > 9) {
			const q = 3 / Math.sqrt(s);
			t[i] = q * a * d[i];
			t[i + 1] = q * b * d[i];
		}
	}
	let out = `M ${pts[0].x} ${pts[0].y}`;
	for (let i = 0; i < n - 1; i++) {
		const h = (pts[i + 1].x - pts[i].x) / 3;
		out += ` C ${pts[i].x + h} ${pts[i].y + t[i] * h}, ${pts[i + 1].x - h} ${pts[i + 1].y - t[i + 1] * h}, ${pts[i + 1].x} ${pts[i + 1].y}`;
	}
	return out;
};

/** Linha que se desenha por trim path, com o ponto viajando na ponta e o valor final ao chegar. */
export const LineChart: React.FC<
	BlockTiming & {
		points: number[];
		/** Rótulos do eixo x, distribuídos de ponta a ponta (dois bastam: início e fim). */
		labels?: string[];
		width?: number;
		height?: number;
		/** Base e topo da escala. Padrão: 0 (ou o menor valor, se negativo) e o maior valor. */
		min?: number;
		max?: number;
		format?: (v: number) => string;
		color?: string;
		area?: boolean;
	}
> = ({points, labels, width, height, min, max, format = (v) => v.toLocaleString('pt-BR'), color = C.accent, area = true, at = 0, out}) => {
	const {u, text} = useFormat();
	const {frame, rise, exit} = useBlock(at, out);
	const id = useId().replace(/[^a-zA-Z0-9]/g, '');
	const w = width ?? text.w;
	const h = height ?? Math.min(text.h, w * 0.56);
	const padT = type.body * u * 1.9;
	const padB = labels ? type.label * u * 2 : 4 * u;
	const plotH = h - padT - padB;
	const plotW = w - 14 * u;
	const lo = min ?? Math.min(0, ...points);
	const hi = max ?? Math.max(...points);
	const {d, len, end} = useMemo(() => {
		const pts = points.map((v, i) => ({
			x: (i / Math.max(1, points.length - 1)) * plotW,
			y: padT + (1 - (v - lo) / (hi - lo || 1)) * plotH,
		}));
		const path = smoothPath(pts);
		return {d: path, len: getLength(path), end: pts[pts.length - 1]};
	}, [points, plotW, plotH, padT, lo, hi]);
	const drawStart = 8;
	const drawLen = 32;
	const draw = rise(drawStart, drawLen, ease.move);
	const tip = getPointAtLength(d, draw * len) ?? end;
	const dot = pop(frame, 30, drawStart, springs.snappy) * (1 - exit);
	const grid = [0, 1, 2, 3];
	return (
		<div style={{position: 'relative', width: w, height: h, fontFamily: FONT}}>
			<svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{position: 'absolute', inset: 0, overflow: 'visible'}}>
				<defs>
					<linearGradient id={`${id}-g`} x1="0" y1="0" x2="0" y2="1">
						<stop offset="0" stopColor={color} stopOpacity={0.2} />
						<stop offset="1" stopColor={color} stopOpacity={0} />
					</linearGradient>
					<clipPath id={`${id}-c`}>
						<rect x={0} y={0} width={Math.max(0, tip.x)} height={h} />
					</clipPath>
				</defs>
				{grid.map((g) => {
					const y = padT + (g / (grid.length - 1)) * plotH;
					return <line key={g} x1={0} y1={y} x2={w} y2={y} stroke={C.line} strokeWidth={2 * u} {...trim(rise(g * 2, dur.base))} />;
				})}
				{area ? <path d={`${d} L ${end.x} ${padT + plotH} L 0 ${padT + plotH} Z`} fill={`url(#${id}-g)`} clipPath={`url(#${id}-c)`} /> : null}
				<path d={d} fill="none" stroke={color} strokeWidth={5 * u} strokeLinecap="round" strokeLinejoin="round" {...trim(draw)} />
				<circle cx={tip.x} cy={tip.y} r={10 * u * dot} fill={color} stroke={C.bg} strokeWidth={4 * u * dot} />
			</svg>
			<div
				style={{
					position: 'absolute',
					right: w - plotW - 10 * u,
					top: end.y - 22 * u,
					transform: 'translateY(-100%)',
					fontSize: type.body * u,
					fontWeight: 700,
					lineHeight: 1.1,
					letterSpacing: '-0.02em',
					fontVariantNumeric: 'tabular-nums',
					color: C.ink,
					whiteSpace: 'nowrap',
				}}
			>
				<Rise p={rise(drawStart + drawLen - 8, dur.base)}>{format(points[points.length - 1])}</Rise>
			</div>
			{labels ? (
				<div
					style={{
						position: 'absolute',
						left: 0,
						top: h - padB + 18 * u,
						width: w,
						display: 'flex',
						justifyContent: 'space-between',
						fontSize: type.label * u,
						fontWeight: 500,
						lineHeight: 1.2,
						color: C.muted,
					}}
				>
					{labels.map((l, i) => (
						<Rise key={i} p={rise(4 + i * 2, dur.base)}>
							{l}
						</Rise>
					))}
				</div>
			) : null}
		</div>
	);
};
