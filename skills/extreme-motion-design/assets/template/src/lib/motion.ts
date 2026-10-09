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

// ---------- Técnicas avançadas (references/techniques-advanced.md) ----------

// Um único overshoot, sem oscilação: só no elemento em foco. Decelerate enfático para heróis de cena.
export const easeX = {
	overshoot: Easing.bezier(0.34, 1.56, 0.64, 1),
	emphasized: Easing.bezier(0.05, 0.7, 0.1, 1),
};

/** Antecipação: recua `back` (fração do percurso) e só então parte para o alvo. */
export const anticipate = (frame: number, start: number, length: number, from: number, to: number, back = 0.08) => {
	const wind = Math.max(2, Math.round(length * 0.25));
	const d = to - from;
	return keys(frame, [start, start + wind, start + length], [from, from - d * back, to], [ease.settle, ease.enter]);
};

/** Follow-through e "follow the leader": o item i repete o líder com atraso (2 a 4 frames por nível). */
export const lag = (frame: number, i: number, delay = 3) => frame - i * delay;

/** Cascata para listas longas: os atrasos se comprimem no fim, e o total nunca passa de `total`. */
export const cascade = (i: number, n: number, total: number, easing: (t: number) => number = Easing.out(Easing.quad)) =>
	n <= 1 ? 0 : Math.round(easing(i / (n - 1)) * total);

/** Squash e stretch preservando volume. amount > 0 estica em Y, < 0 achata. */
export const squash = (amount: number) => {
	const sy = 1 + amount;
	return {sx: 1 / sy, sy};
};

/** Velocidade por frame de qualquer função do frame (para smear, blur direcional e conferência de curva). */
export const velocity = (fn: (f: number) => number, frame: number) => fn(frame + 0.5) - fn(frame - 0.5);

/** Smear: fator de esticamento na direção do movimento. 1 abaixo do limiar, até `max` no pico. */
export const smear = (pxPerFrame: number, threshold = 40, max = 3) =>
	Math.min(max, 1 + Math.max(0, Math.abs(pxPerFrame) - threshold) / threshold);

/**
 * Speed ramp (time remap): devolve o tempo local em frames dado um perfil de velocidade.
 * speeds: [[frame, velocidade]], interpolado linearmente. Ex.: [[0, 4], [12, 0.25], [40, 1]].
 */
export const timeRemap = (frame: number, speeds: Array<[number, number]>) => {
	let t = 0;
	for (let i = 0; i < speeds.length; i++) {
		const [f0, s0] = speeds[i];
		const next = speeds[i + 1];
		if (!next || frame <= next[0]) {
			const dt = Math.max(0, frame - f0);
			if (!next) return t + s0 * dt;
			const s = s0 + ((next[1] - s0) * dt) / (next[0] - f0);
			return t + ((s0 + s) / 2) * dt;
		}
		t += ((s0 + next[1]) / 2) * (next[0] - f0);
	}
	return t;
};

/** Onda triangular 0..1..0 (loopOut pingpong). */
export const pingPong = (frame: number, period: number) => 1 - Math.abs(loopPhase(frame, period) * 2 - 1);

/** Contador que assenta sem piscar: use com fontVariantNumeric 'tabular-nums'. */
export const ticker = (frame: number, start: number, length: number, from: number, to: number) =>
	Math.round(tween(frame, start, length, from, to, ease.settle));
