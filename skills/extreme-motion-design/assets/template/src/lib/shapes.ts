import {random} from 'remotion';

type P = {x: number; y: number};

const closedCurve = (pts: P[]) => {
	// Catmull-Rom fechado convertido em Bézier cúbica: contorno orgânico e suave.
	const n = pts.length;
	let d = `M ${pts[0].x.toFixed(2)},${pts[0].y.toFixed(2)}`;
	for (let i = 0; i < n; i++) {
		const p0 = pts[(i - 1 + n) % n];
		const p1 = pts[i];
		const p2 = pts[(i + 1) % n];
		const p3 = pts[(i + 2) % n];
		const c1 = {x: p1.x + (p2.x - p0.x) / 6, y: p1.y + (p2.y - p0.y) / 6};
		const c2 = {x: p2.x - (p3.x - p1.x) / 6, y: p2.y - (p3.y - p1.y) / 6};
		d += ` C ${c1.x.toFixed(2)},${c1.y.toFixed(2)} ${c2.x.toFixed(2)},${c2.y.toFixed(2)} ${p2.x.toFixed(2)},${p2.y.toFixed(2)}`;
	}
	return d + ' Z';
};

export const circlePath = (cx: number, cy: number, r: number, n = 12) =>
	closedCurve(
		Array.from({length: n}, (_, i) => {
			const a = (i / n) * Math.PI * 2;
			return {x: cx + Math.cos(a) * r * 1.0, y: cy + Math.sin(a) * r * 1.0};
		}),
	);

export const starPath = (cx: number, cy: number, r: number, points = 5, inner = 0.45) => {
	const pts: string[] = [];
	for (let i = 0; i < points * 2; i++) {
		const a = (i / (points * 2)) * Math.PI * 2 - Math.PI / 2;
		const rr = i % 2 === 0 ? r : r * inner;
		pts.push(`${(cx + Math.cos(a) * rr).toFixed(2)},${(cy + Math.sin(a) * rr).toFixed(2)}`);
	}
	return `M ${pts.join(' L ')} Z`;
};

export const blobPath = (cx: number, cy: number, r: number, seed: string, n = 8, variance = 0.28) =>
	closedCurve(
		Array.from({length: n}, (_, i) => {
			const a = (i / n) * Math.PI * 2;
			const rr = r * (1 - variance / 2 + random(`${seed}-${i}`) * variance);
			return {x: cx + Math.cos(a) * rr, y: cy + Math.sin(a) * rr};
		}),
	);

export const roundedRectPath = (x: number, y: number, w: number, h: number, r: number) =>
	`M ${x + r},${y} H ${x + w - r} Q ${x + w},${y} ${x + w},${y + r} V ${y + h - r} Q ${x + w},${y + h} ${x + w - r},${y + h} H ${x + r} Q ${x},${y + h} ${x},${y + h - r} V ${y + r} Q ${x},${y} ${x + r},${y} Z`;
