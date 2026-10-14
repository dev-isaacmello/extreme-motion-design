import React, {useMemo} from 'react';
import {useFormat} from '../lib/format';
import {dur, easeX} from '../lib/motion';
import {C, MONO} from '../theme';
import {BlockTiming, mix, surface, useBlock} from './shared';

type Tok = {t: string; c: string};

const KEYWORDS = new Set(
	'const let var function return import from export default if else for while await async class new def in of type interface true false null undefined None True False'.split(' '),
);
// Ordem importa: string antes de comentário, para barras e cerquilha dentro de aspas não virarem comentário.
const TOKEN = /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`[^`]*`)|(\/\/.*$|#.*$)|(\b\d[\d_.]*\b)|([A-Za-z_$][\w$]*)|(\s+|.)/g;

const tokenize = (line: string): Tok[] =>
	Array.from(line.matchAll(TOKEN), (m) => ({
		t: m[0],
		c: m[1] ? C.second : m[2] ? C.muted : m[3] ? C.second : m[4] && KEYWORDS.has(m[4]) ? C.accent : C.ink,
	}));

/**
 * Janela de código ou de terminal com digitação determinística: o caractere visível sai do frame.
 * No terminal, só as linhas que começam com `prompt` são digitadas; as demais são saída e entram inteiras.
 */
export const CodeWindow: React.FC<
	BlockTiming & {
		code: string;
		variant?: 'code' | 'terminal';
		title?: string;
		/** Caracteres por segundo. */
		cps?: number;
		prompt?: string;
		width?: number;
		fontSize?: number;
	}
> = ({code, variant = 'code', title, cps = 32, prompt = '$ ', width, fontSize = 30, at = 0, out}) => {
	const {u, text} = useFormat();
	const {frame, rise} = useBlock(at, out);
	const terminal = variant === 'terminal';
	const perFrame = cps / 30;
	const typeStart = 12;
	const rows = useMemo(() => {
		let t = typeStart;
		return code.split('\n').map((line) => {
			const typed = !terminal || line.startsWith(prompt);
			const fixed = terminal && typed ? prompt.length : 0;
			const start = t;
			t += typed ? (line.length - fixed) / perFrame + 5 : 3;
			const toks: Tok[] = terminal
				? typed
					? [{t: prompt, c: C.accent}, {t: line.slice(prompt.length), c: C.ink}]
					: [{t: line, c: C.muted}]
				: tokenize(line);
			return {toks, len: line.length, start, typed, fixed};
		});
	}, [code, terminal, prompt, perFrame]);

	const w = width ?? Math.min(text.w, 1100 * u);
	// A fonte encolhe até a linha mais longa caber: JetBrains Mono ocupa 0,6 em por caractere.
	const cols = Math.max(...rows.map((r) => r.len)) + (terminal ? 1.5 : 5.2);
	const size = Math.min(fontSize * u, (w - 64 * u) / (cols * 0.6));
	const lineH = size * 1.6;
	const active = rows.reduce((last, r, i) => (frame >= r.start ? i : last), 0);
	const typing = rows[active].typed && frame < rows[active].start + (rows[active].len - rows[active].fixed) / perFrame;
	const blink = typing || Math.floor(Math.max(0, frame) / 15) % 2 === 0;
	const dot = 14 * u;
	return (
		<div
			style={{
				...surface(rise(0, dur.slow, easeX.emphasized), u),
				width: w,
				borderRadius: 20 * u,
				overflow: 'hidden',
				background: mix(C.ink, C.bg, 0.05),
				boxShadow: `0 ${36 * u}px ${90 * u}px rgba(0, 0, 0, 0.5), inset 0 0 0 ${1.5 * u}px ${mix(C.ink, C.bg, 0.18)}`,
				fontFamily: MONO,
			}}
		>
			<div data-decor style={{position: 'relative', height: 60 * u, display: 'flex', alignItems: 'center', padding: `0 ${24 * u}px`, gap: 10 * u}}>
				{[0, 1, 2].map((i) => (
					<div key={i} style={{width: dot, height: dot, borderRadius: dot, background: mix(C.ink, C.bg, 0.24)}} />
				))}
				<div style={{position: 'absolute', left: 0, right: 0, textAlign: 'center', fontSize: 20 * u, color: C.muted}}>
					{title ?? (terminal ? 'terminal' : 'exemplo.ts')}
				</div>
			</div>
			<div style={{padding: `${14 * u}px ${32 * u}px ${30 * u}px`, fontSize: size, lineHeight: `${lineH}px`, whiteSpace: 'pre', overflow: 'hidden'}}>
				{rows.map((r, i) => {
					const shown = r.typed ? Math.min(r.len, Math.max(0, r.fixed + Math.floor((frame - r.start) * perFrame))) : r.len;
					const visible = frame >= r.start || (i === 0 && frame >= typeStart - 6);
					let left = visible ? shown : 0;
					return (
						<div key={i} style={{height: lineH, display: 'flex'}}>
							{terminal ? null : (
								<span data-decor style={{width: size * 2.2, flexShrink: 0, color: mix(C.muted, C.bg, 0.55)}}>
									{i + 1}
								</span>
							)}
							{r.toks.map((tok, j) => {
								const part = tok.t.slice(0, left);
								left -= part.length;
								return part ? (
									<span key={j} style={{color: tok.c}}>
										{part}
									</span>
								) : null;
							})}
							{i === active ? (
								<span
									style={{
										width: size * 0.56,
										height: size * 1.15,
										alignSelf: 'center',
										marginLeft: size * 0.06,
										background: C.accent,
										visibility: blink ? 'visible' : 'hidden',
									}}
								/>
							) : null}
						</div>
					);
				})}
			</div>
		</div>
	);
};
