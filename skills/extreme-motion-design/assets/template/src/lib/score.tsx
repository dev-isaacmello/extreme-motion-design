import React from 'react';
import {Sequence, useCurrentFrame, useVideoConfig} from 'remotion';
import timeline from '../../public/timeline.json';
import cues from '../../public/cues.json';

// Partitura (timeline.json) e marcas (cues.json), as duas escritas por scripts/score.py a partir do roteiro.json.
// Cena nenhuma guarda frame escrito à mão: todo tempo sai daqui.

export type SceneId = (typeof timeline.scenes)[number]['id'];
export type Cue = keyof typeof cues.ev;
export type Word = {word: string; start: number; end: number};

export const WORDS = cues.words as Word[];
export const BEATS = cues.beats as number[];
export const sceneOf = (id: string) => {
	const s = timeline.scenes.find((x) => x.id === id);
	if (!s) throw new Error(`cena "${id}" não existe em timeline.json`);
	return s;
};
/** Segundo absoluto de uma marca do roteiro. */
export const cue = (name: Cue) => (cues.ev as Record<string, number>)[name];
/** Palavras da narração ditas dentro da cena (tempos absolutos). */
export const wordsOf = (id: string) => {
	const s = sceneOf(id);
	return WORDS.filter((w) => w.start >= s.start - 0.02 && w.start < s.end);
};

/**
 * Relógio da cena. Use dentro de <Scene id>: `frame` é local, `len` é a duração em frames,
 * `at('marca', +3)` é o frame local de uma marca do roteiro e `sec(t)` o de um segundo absoluto.
 */
export const useScene = (id: string) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const s = sceneOf(id);
	const start = Math.round(s.start * fps);
	const len = Math.round(s.end * fps) - start;
	const sec = (t: number) => Math.round(t * fps) - start;
	const at = (name: Cue, off = 0) => sec(cue(name)) + off;
	return {frame, fps, len, at, sec, since: (name: Cue) => frame - at(name), words: wordsOf(id)};
};

/** Monta a cena no trecho que a partitura dá a ela. Os filhos leem o relógio com useScene(id). */
export const Scene: React.FC<{id: string; children: React.ReactNode; overlap?: number}> = ({id, children, overlap = 0}) => {
	const {fps} = useVideoConfig();
	const s = sceneOf(id);
	const from = Math.round(s.start * fps);
	return (
		<Sequence from={from} durationInFrames={Math.round(s.end * fps) - from + overlap} name={id}>
			{children}
		</Sequence>
	);
};
