import {interpolate as flubber} from 'flubber';

const cache = new Map<string, (t: number) => string>();

const pair = (a: string, b: string) => {
	const key = `${a}|${b}`;
	if (!cache.has(key)) cache.set(key, flubber(a, b, {maxSegmentLength: 3}));
	return cache.get(key)!;
};

/**
 * Morphing entre formas SVG. progress vai de 0 a paths.length - 1:
 * 0 = primeira forma, 1 = segunda, 1.5 = meio caminho entre a segunda e a terceira.
 * Segure cada forma (hold) e transicione com ease.move; morph contínuo cansa.
 */
export const morphPath = (paths: string[], progress: number) => {
	const p = Math.max(0, Math.min(paths.length - 1, progress));
	const i = Math.min(Math.floor(p), paths.length - 2);
	return pair(paths[i], paths[i + 1])(p - i);
};
