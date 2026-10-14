import {useVideoConfig} from 'remotion';

// Formatos de entrega. O mesmo projeto renderiza nos três: `render.py --formats reels,square,youtube`.
export const FORMATS = {
	youtube: {width: 1920, height: 1080},
	reels: {width: 1080, height: 1920},
	square: {width: 1080, height: 1080},
} as const;
export type FormatName = keyof typeof FORMATS;

type Box = {x: number; y: number; w: number; h: number};

/**
 * Formato da composição atual. `u` é a unidade de escala (1 em 1080 px no lado menor): escreva tamanhos como
 * `96 * u`. `text` e `action` são as áreas seguras em px. `pick` escolhe um valor por formato.
 */
export const useFormat = () => {
	const {width, height} = useVideoConfig();
	const ratio = width / height;
	const name: FormatName = ratio < 0.8 ? 'reels' : ratio < 1.25 ? 'square' : 'youtube';
	const u = Math.min(width, height) / 1080;
	// Em 9:16 a interface do app cobre o topo e o rodapé: texto entre y 360 e 1420 de 1920.
	const text: Box =
		name === 'reels'
			? {x: width * 0.1, y: height * (360 / 1920), w: width * 0.8, h: height * ((1420 - 360) / 1920)}
			: {x: width * 0.1, y: height * 0.1, w: width * 0.8, h: height * 0.8};
	const action: Box = {x: width * 0.05, y: height * 0.05, w: width * 0.9, h: height * 0.9};
	const pick = <T,>(by: {youtube: T; reels?: T; square?: T}): T => by[name] ?? by.youtube;
	return {width, height, name, vertical: name === 'reels', square: name === 'square', u, text, action, pick};
};
