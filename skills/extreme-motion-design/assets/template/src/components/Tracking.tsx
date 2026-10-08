import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';

// Formatos gerados por scripts/track.py e scripts/matchmove.py.
export type PointTrack = {fps: number; frames: Array<{f: number; x: number; y: number}>};
export type CornerTrack = {fps: number; frames: Array<{f: number; corners: number[]}>}; // [x0,y0,...,x3,y3] TL TR BR BL

const sample = <T,>(frames: Array<{f: number} & T>, frame: number, pick: (a: T) => number[]) => {
	if (frame <= frames[0].f) return pick(frames[0]);
	const last = frames[frames.length - 1];
	if (frame >= last.f) return pick(last);
	let i = 0;
	while (frames[i + 1].f < frame) i++;
	const a = pick(frames[i]);
	const b = pick(frames[i + 1]);
	const t = (frame - frames[i].f) / (frames[i + 1].f - frames[i].f);
	return a.map((v, k) => v + (b[k] - v) * t);
};

/** Gruda os filhos num ponto rastreado (motion tracking). */
export const Tracked: React.FC<{track: PointTrack; offset?: {x: number; y: number}; children: React.ReactNode}> = ({
	track,
	offset = {x: 0, y: 0},
	children,
}) => {
	const frame = useCurrentFrame();
	const [x, y] = sample(track.frames, frame, (p) => [p.x, p.y]);
	return (
		<div style={{position: 'absolute', left: x + offset.x, top: y + offset.y, transform: 'translate(-50%, -50%)'}}>
			{children}
		</div>
	);
};

/** Homografia quadrado unitário -> quadrilátero (Heckbert), em CSS matrix3d. */
export const cornerPinMatrix = (w: number, h: number, c: number[]) => {
	const [x0, y0, x1, y1, x2, y2, x3, y3] = c;
	const sx = x0 - x1 + x2 - x3;
	const sy = y0 - y1 + y2 - y3;
	const dx1 = x1 - x2;
	const dx2 = x3 - x2;
	const dy1 = y1 - y2;
	const dy2 = y3 - y2;
	const den = dx1 * dy2 - dx2 * dy1;
	const g = den === 0 ? 0 : (sx * dy2 - dx2 * sy) / den;
	const hh = den === 0 ? 0 : (dx1 * sy - sx * dy1) / den;
	const a = x1 - x0 + g * x1;
	const b = x3 - x0 + hh * x3;
	const d = y1 - y0 + g * y1;
	const e = y3 - y0 + hh * y3;
	return `matrix3d(${a / w},${d / w},0,${g / w},${b / h},${e / h},0,${hh / h},0,0,1,0,${x0},${y0},0,1)`;
};

/** Corner pin: cola uma tela ou imagem num plano rastreado (match moving 2D). */
export const CornerPin: React.FC<{
	track: CornerTrack;
	width: number;
	height: number;
	children: React.ReactNode;
}> = ({track, width, height, children}) => {
	const frame = useCurrentFrame();
	const c = sample(track.frames, frame, (p) => p.corners);
	return (
		<div style={{position: 'absolute', left: 0, top: 0, width, height, transformOrigin: '0 0', transform: cornerPinMatrix(width, height, c)}}>
			{children}
		</div>
	);
};

export const progressBetween = (frame: number, a: number, b: number) =>
	interpolate(frame, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
