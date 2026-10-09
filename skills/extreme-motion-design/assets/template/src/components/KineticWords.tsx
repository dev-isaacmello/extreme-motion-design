import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {clamp, ease, springs} from '../lib/motion';

export type Word = {word: string; start: number; end: number};

/** Agrupa palavras em frases curtas por pontuação, pausa longa ou limite de palavras. */
export const groupPhrases = (words: Word[], maxWords = 4, gap = 0.35): Word[][] => {
	const groups: Word[][] = [];
	let cur: Word[] = [];
	words.forEach((w, i) => {
		cur.push(w);
		const next = words[i + 1];
		const punct = /[.,;:!?…]$/.test(w.word);
		if (!next || punct || cur.length >= maxWords || next.start - w.end > gap) {
			groups.push(cur);
			cur = [];
		}
	});
	return groups;
};

/**
 * Tipografia cinética sincronizada à narração (tempos de words.json).
 * Cada palavra sobe por uma máscara `lead` frames antes de ser falada; a palavra falada ganha o acento.
 * Com tempos vindos do align.py (que já adianta ~0,1 s), use lead={0}.
 */
export const KineticWords: React.FC<{
	words: Word[];
	offsetSec?: number;
	fontSize?: number;
	color?: string;
	accent?: string;
	top?: string;
	maxWords?: number;
	weight?: number;
	lead?: number;
}> = ({words, offsetSec = 0, lead = 3, fontSize = 96, color = '#F5F2EA', accent = '#FFB547', top = '50%', maxWords = 4, weight = 700}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps - offsetSec;
	const groups = groupPhrases(words, maxWords);
	const idx = groups.findIndex((g, i) => {
		const end = groups[i + 1] ? groups[i + 1][0].start - 0.05 : g[g.length - 1].end + 0.8;
		return t >= g[0].start - 0.2 && t < end;
	});
	if (idx < 0) return null;
	const group = groups[idx];
	const groupEnd = groups[idx + 1] ? groups[idx + 1][0].start - 0.05 : group[group.length - 1].end + 0.8;
	const exit = interpolate(t, [groupEnd - 0.18, groupEnd], [0, 1], {...clamp, easing: ease.exit});
	return (
		<AbsoluteFill>
			<div
				style={{
					position: 'absolute',
					top,
					left: '11%',
					width: '78%',
					transform: 'translateY(-50%)',
					display: 'flex',
					flexWrap: 'wrap',
					justifyContent: 'center',
					columnGap: fontSize * 0.26,
					fontSize,
					fontWeight: weight,
					lineHeight: 1.06,
					letterSpacing: '-0.025em',
					color,
				}}
			>
				{group.map((w, i) => {
					const startF = Math.round((w.start + offsetSec) * fps) - lead;
					const p = spring({frame: frame - startF, fps, config: springs.smooth, durationInFrames: 14});
					const y = interpolate(p, [0, 1], [105, 0]) - exit * 105;
					const spoken = t >= w.start - 0.02 && t <= w.end + 0.06;
					return (
						<span key={`${idx}-${i}`} style={{display: 'inline-block', overflow: 'hidden', paddingBottom: '0.1em'}}>
							<span
								style={{
									display: 'inline-block',
									transform: `translateY(${y}%)`,
									color: spoken ? accent : color,
								}}
							>
								{w.word}
							</span>
						</span>
					);
				})}
			</div>
		</AbsoluteFill>
	);
};
