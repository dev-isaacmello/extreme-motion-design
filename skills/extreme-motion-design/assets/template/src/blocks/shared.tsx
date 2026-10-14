import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {dur, ease, tween} from '../lib/motion';

export type BlockTiming = {
	/** Frame local em que o bloco começa a entrar. */
	at?: number;
	/** Frame local em que o bloco já terminou de sair. A saída começa EXIT frames antes. */
	out?: number;
};

// A saída dura cerca de 75% da entrada base (doutrina). Em frames a 30 fps.
export const EXIT = Math.round(dur.base * 0.75);

/**
 * Relógio do bloco. `frame` é local a `at` e normalizado para 30 fps, então os atrasos internos
 * valem para qualquer fps. `rise(atraso, duração)` devolve o progresso 0..1 de uma entrada e já
 * desconta a saída: o mesmo valor fecha a máscara ou recolhe o traço quando `out` chega.
 */
export const useBlock = (at = 0, out?: number) => {
	const abs = useCurrentFrame();
	const {fps} = useVideoConfig();
	const k = fps / 30;
	const frame = (abs - at) / k;
	const exit = out === undefined ? 0 : tween(abs, out - EXIT * k, EXIT * k, 0, 1, ease.exit);
	const rise = (delay = 0, length: number = dur.base, easing: (t: number) => number = ease.enter) =>
		Math.min(tween(frame, delay, length, 0, 1, easing), 1 - exit);
	return {frame, fps, k, exit, rise};
};

export const mix = (a: string, b: string, t: number) => `color-mix(in srgb, ${a} ${Math.round(t * 100)}%, ${b})`;
export const alpha = (c: string, a: number) => mix(c, 'transparent', a);

/** Entrada de superfície (janela, aparelho): sobe e cresce; a opacidade só cobre os 2 primeiros frames. */
export const surface = (p: number, u: number): React.CSSProperties => ({
	transform: `translateY(${(1 - p) * 56 * u}px) scale(${0.94 + 0.06 * p})`,
	opacity: Math.min(1, p * 3),
});

/** Trim path: espalhe num <path>, <line> ou <circle>. Some por inteiro em 0 para a ponta redonda não deixar ponto. */
export const trim = (p: number) => ({
	pathLength: 1,
	strokeDasharray: 1,
	strokeDashoffset: 1 - p,
	visibility: p < 0.002 ? ('hidden' as const) : ('visible' as const),
});

/** Quebra o texto em linhas de até `max` caracteres, sem cortar palavra. */
export const wrap = (text: string, max: number): string[] => {
	const lines: string[] = [];
	let cur = '';
	for (const w of text.split(/\s+/).filter(Boolean)) {
		if (cur && cur.length + 1 + w.length > max) {
			lines.push(cur);
			cur = w;
		} else {
			cur = cur ? `${cur} ${w}` : w;
		}
	}
	if (cur) lines.push(cur);
	return lines;
};

/** Subida por máscara (baseline reveal) de uma linha. A folga embaixo evita cortar g, p e ç; a de cima, o acento de Ã, É e Ç em entrelinha apertada. */
export const Rise: React.FC<{p: number; children: React.ReactNode; style?: React.CSSProperties}> = ({p, children, style}) => (
	<span style={{display: 'block', overflow: 'hidden', paddingBottom: '0.14em', marginBottom: '-0.14em', paddingTop: '0.34em', marginTop: '-0.34em', ...style}}>
		<span style={{display: 'block', transform: `translateY(${(1 - Math.min(1, Math.max(0, p))) * 150}%)`}}>{children}</span>
	</span>
);
