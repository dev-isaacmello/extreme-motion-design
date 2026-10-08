import {Easing, interpolate, random, spring} from 'remotion';
import {noise2D} from '@remotion/noise';

// Tokens de movimento. Componentes usam estes nomes; não invente curva por cena.
export const ease = {
	enter: Easing.bezier(0.16, 1, 0.3, 1), // entradas: rápido no começo, assenta suave
	sharp: Easing.bezier(0.2, 0.75, 0.34, 0.94), // entrada mais seca para UI e texto curto
	settle: Easing.bezier(0, 0.65, 0.51, 0.99), // assentar sem overshoot (zoom out, reveal)
	move: Easing.bezier(0.77, 0, 0.175, 1), // mudar de posição ou de forma (in-out forte)
	exit: Easing.bezier(0.7, 0, 0.84, 0), // saídas aceleram e somem
	linear: Easing.linear, // só para rotação contínua e loops
};

export const springs = {
	smooth: {damping: 200}, // sem overshoot, padrão para texto
	snappy: {damping: 20, stiffness: 200}, // overshoot leve, UI e ícones
	bouncy: {damping: 12, stiffness: 180, mass: 0.8}, // só no elemento em foco
	heavy: {damping: 15, stiffness: 80, mass: 2}, // objetos grandes, logos
};

// Durações em frames a 30 fps. Escale com fps / 30 se mudar o fps.
export const dur = {micro: 6, fast: 10, base: 16, slow: 24, scene: 90};

export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const sec = (s: number, fps: number) => Math.round(s * fps);

/** Keyframe simples: de `from` para `to` entre start e start + length. */
export const tween = (
	frame: number,
	start: number,
	length: number,
	from: number,
	to: number,
	easing: (t: number) => number = ease.enter,
) => interpolate(frame, [start, start + length], [from, to], {...clamp, easing});

/** Keyframes com easing por segmento: frames e valores do mesmo tamanho. */
export const keys = (
	frame: number,
	frames: number[],
	values: number[],
	easings: Array<(t: number) => number> = [],
) => {
	if (frame <= frames[0]) return values[0];
	for (let i = 0; i < frames.length - 1; i++) {
		if (frame <= frames[i + 1]) {
			return interpolate(frame, [frames[i], frames[i + 1]], [values[i], values[i + 1]], {
				...clamp,
				easing: easings[i] ?? ease.move,
			});
		}
	}
	return values[values.length - 1];
};

/** Spring 0 -> 1 começando em `start`. */
export const pop = (frame: number, fps: number, start = 0, config = springs.snappy) =>
	spring({frame: frame - start, fps, config});

/** Atraso de stagger: distribui `total` frames entre n itens. */
export const stagger = (i: number, n: number, total: number) => (n <= 1 ? 0 : Math.round((i * total) / (n - 1)));

/** Tempo em degraus: animar em twos ou threes (cel, stop motion, frame a frame). */
export const stepped = (frame: number, step = 2) => Math.floor(frame / step) * step;

/** Fase 0..1 de um loop de `period` frames. O frame `period` repete o frame 0. */
export const loopPhase = (frame: number, period: number) => (((frame % period) + period) % period) / period;

/** Ruído que fecha o loop: amostra o noise num círculo. */
export const loopNoise = (seed: string, frame: number, period: number, radius = 1) => {
	const a = loopPhase(frame, period) * Math.PI * 2;
	return noise2D(seed, Math.cos(a) * radius, Math.sin(a) * radius);
};

/** Tremor orgânico determinístico (câmera na mão, deriva). */
export const wiggle = (seed: string, frame: number, freq = 0.05, amp = 1) => noise2D(seed, frame * freq, 0) * amp;

/** Jitter de stop motion: só muda a cada `hold` frames. */
export const jitter = (seed: string, frame: number, hold = 2, amp = 1) =>
	(random(`${seed}-${Math.floor(frame / hold)}`) - 0.5) * 2 * amp;
