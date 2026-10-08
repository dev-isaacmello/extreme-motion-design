export type P = {x: number; y: number};

/** IK de dois ossos (braço, perna). bend = 1 ou -1 escolhe o lado do cotovelo. */
export const twoBoneIK = (root: P, target: P, l1: number, l2: number, bend = 1) => {
	const dx = target.x - root.x;
	const dy = target.y - root.y;
	const dist = Math.min(Math.max(Math.hypot(dx, dy), Math.abs(l1 - l2) + 0.001), l1 + l2 - 0.001);
	const base = Math.atan2(dy, dx);
	const cosA = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist);
	const a = Math.acos(Math.min(1, Math.max(-1, cosA)));
	const upper = base - bend * a;
	const elbow = {x: root.x + l1 * Math.cos(upper), y: root.y + l1 * Math.sin(upper)};
	const hand = {x: root.x + dist * Math.cos(base), y: root.y + dist * Math.sin(base)};
	return {elbow, hand, upperAngle: upper, lowerAngle: Math.atan2(hand.y - elbow.y, hand.x - elbow.x)};
};

/**
 * FABRIK para cadeias (cauda, tentáculo, corda). Recebe a pose de repouso a cada frame,
 * sem estado entre frames, para o render continuar determinístico.
 */
export const fabrik = (rest: P[], target: P, iterations = 12): P[] => {
	const pts = rest.map((p) => ({...p}));
	const lens = pts.slice(1).map((p, i) => Math.hypot(p.x - pts[i].x, p.y - pts[i].y));
	const root = {...pts[0]};
	const reach = lens.reduce((a, b) => a + b, 0);
	const lerp = (a: P, b: P, t: number) => ({x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t});
	if (Math.hypot(target.x - root.x, target.y - root.y) >= reach) {
		for (let i = 0; i < lens.length; i++) {
			const d = Math.hypot(target.x - pts[i].x, target.y - pts[i].y) || 1e-6;
			pts[i + 1] = lerp(pts[i], target, lens[i] / d);
		}
		return pts;
	}
	for (let k = 0; k < iterations; k++) {
		pts[pts.length - 1] = {...target};
		for (let i = pts.length - 2; i >= 0; i--) {
			const d = Math.hypot(pts[i + 1].x - pts[i].x, pts[i + 1].y - pts[i].y) || 1e-6;
			pts[i] = lerp(pts[i + 1], pts[i], lens[i] / d);
		}
		pts[0] = {...root};
		for (let i = 0; i < pts.length - 1; i++) {
			const d = Math.hypot(pts[i + 1].x - pts[i].x, pts[i + 1].y - pts[i].y) || 1e-6;
			pts[i + 1] = lerp(pts[i], pts[i + 1], lens[i] / d);
		}
	}
	return pts;
};

/** Hierarquia FK: cada osso herda a rotação do pai. angles em graus, relativos ao pai. */
export const forwardKinematics = (root: P, lengths: number[], angles: number[]): P[] => {
	const out: P[] = [{...root}];
	let acc = 0;
	for (let i = 0; i < lengths.length; i++) {
		acc += (angles[i] * Math.PI) / 180;
		const prev = out[i];
		out.push({x: prev.x + Math.cos(acc) * lengths[i], y: prev.y + Math.sin(acc) * lengths[i]});
	}
	return out;
};

/** Fonema (IPA do espeak/Kokoro) -> visema simples para boca 2D. */
export const visemeFor = (ph: string): 'rest' | 'A' | 'E' | 'I' | 'O' | 'U' | 'MBP' | 'FV' | 'L' | 'cons' => {
	if (/[mbp]/.test(ph)) return 'MBP';
	if (/[fv]/.test(ph)) return 'FV';
	if (/[lʎɾr]/.test(ph)) return 'L';
	if (/[aɐã]/.test(ph)) return 'A';
	if (/[eɛẽ]/.test(ph)) return 'E';
	if (/[iɪĩj]/.test(ph)) return 'I';
	if (/[oɔõ]/.test(ph)) return 'O';
	if (/[uʊũw]/.test(ph)) return 'U';
	if (ph.trim() === '') return 'rest';
	return 'cons';
};
