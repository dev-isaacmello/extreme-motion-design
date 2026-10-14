import React from 'react';
import {AbsoluteFill} from 'remotion';
import {useFormat} from '../lib/format';
import {ease, keys, pop, springs, tween} from '../lib/motion';
import {C} from '../theme';
import {useBlock} from './shared';

/**
 * x e y em px do quadro. `at` é o frame do evento: a chegada ao ponto ou, com `click`, o clique
 * (o cursor chega CLICK_PAUSE frames antes e espera).
 */
export type CursorPoint = {x: number; y: number; at: number; click?: boolean};

export const CLICK_PAUSE = 5;

/** Cursor de demo: viaja em arco entre os pontos, pausa, clica com escala e ripple. */
export const Cursor: React.FC<{
	path: CursorPoint[];
	/** Altura da seta em px do quadro de 1080 (multiplicada por u). */
	size?: number;
	color?: string;
	/** Frame em que o cursor terminou de sair. */
	out?: number;
}> = ({path, size = 52, color = C.ink, out}) => {
	const {u} = useFormat();
	const {frame, k, exit} = useBlock(0, out);
	if (!path.length) return null;
	const pts = path.map((p) => ({...p, f: p.at / k, arrive: p.at / k - (p.click ? CLICK_PAUSE : 0)}));
	let x = pts[0].x;
	let y = pts[0].y;
	for (let i = 1; i < pts.length; i++) {
		const a = pts[i - 1];
		const b = pts[i];
		const dx = b.x - a.x;
		const dy = b.y - a.y;
		const dist = Math.hypot(dx, dy) || 1;
		// Distância maior pede mais tempo: 10 a 26 frames.
		const travel = Math.min(26, Math.max(10, Math.round(dist / (36 * u))));
		const start = Math.min(Math.max(a.f + (a.click ? 8 : 2), b.arrive - travel), b.arrive - 4);
		if (frame < start) break;
		const t = tween(frame, start, b.arrive - start, 0, 1, ease.move);
		const bow = Math.sin(t * Math.PI) * dist * 0.12;
		// O arco sempre abre para cima, como a mão faz.
		const side = -dx / dist > 0 ? -1 : 1;
		x = a.x + dx * t + (dy / dist) * side * bow;
		y = a.y + dy * t + (-dx / dist) * side * bow;
	}
	const clicks = pts.filter((p) => p.click);
	const press = clicks.reduce((s, c) => s * keys(frame, [c.f - 3, c.f, c.f + 5], [1, 0.84, 1], [ease.sharp, ease.settle]), 1);
	const shown = Math.min(pop(frame, 30, pts[0].arrive - 8, springs.snappy), 1.2) * (1 - exit);
	const h = size * u;
	const ring = h * 1.5;
	return (
		<AbsoluteFill style={{pointerEvents: 'none'}}>
			{clicks.map((c, i) => {
				const t = tween(frame, c.f, 14, 0, 1, ease.settle);
				if (frame < c.f || t >= 1) return null;
				return (
					<div
						key={i}
						style={{
							position: 'absolute',
							left: 0,
							top: 0,
							width: ring * 2,
							height: ring * 2,
							borderRadius: ring,
							boxSizing: 'border-box',
							border: `${3 * u}px solid ${color}`,
							transform: `translate(${c.x - ring}px, ${c.y - ring}px) scale(${0.2 + 0.8 * t})`,
							opacity: (1 - t) * 0.7,
						}}
					/>
				);
			})}
			<svg
				width={(h * 36) / 56}
				height={h}
				viewBox="0 0 36 56"
				style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', transform: `translate(${x}px, ${y}px) scale(${shown * press})`, transformOrigin: '0 0'}}
			>
				<path d="M0,0 L0,46 L12,34 L22,56 L30,52 L20,31 L36,31 Z" fill={color} stroke={C.bg} strokeWidth={3} strokeLinejoin="round" />
			</svg>
		</AbsoluteFill>
	);
};
