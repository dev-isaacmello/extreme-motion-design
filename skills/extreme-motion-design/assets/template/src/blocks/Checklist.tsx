import React from 'react';
import {useFormat} from '../lib/format';
import {cascade, dur, ease, stagger} from '../lib/motion';
import {C, FONT, type} from '../theme';
import {BlockTiming, Rise, trim, useBlock} from './shared';

/** Lista em cascata: cada linha sobe por máscara e depois o check se desenha por traço, um a um. */
export const Checklist: React.FC<
	BlockTiming & {
		items: string[];
		/** Quantos itens ganham o check, do primeiro em diante. Padrão: todos. */
		done?: number;
		width?: number;
		fontSize?: number;
		accent?: string;
	}
> = ({items, done, width, fontSize = type.body, accent = C.accent, at = 0, out}) => {
	const {u, text} = useFormat();
	const {rise} = useBlock(at, out);
	const n = items.length;
	const checked = Math.min(n, done ?? n);
	const size = fontSize * u;
	const box = size * 1.1;
	const checksFrom = 12 + dur.base - 4;
	return (
		<div style={{width: width ?? Math.min(text.w, 900 * u), display: 'flex', flexDirection: 'column', gap: size * 0.62, fontFamily: FONT}}>
			{items.map((item, i) => {
				const start = cascade(i, n, 12);
				const isDone = i < checked;
				const check = isDone ? rise(checksFrom + stagger(i, checked, Math.min(15, 5 * (checked - 1))), dur.fast, ease.sharp) : 0;
				return (
					<div key={i} style={{display: 'flex', alignItems: 'center', gap: size * 0.55}}>
						<svg width={box} height={box} viewBox="0 0 48 48" style={{flexShrink: 0, transform: `scale(${rise(start, dur.base)})`}}>
							<circle cx={24} cy={24} r={21} fill="none" stroke={C.line} strokeWidth={3} />
							<circle cx={24} cy={24} r={21} fill="none" stroke={accent} strokeWidth={3} transform="rotate(-90 24 24)" {...trim(check)} />
							<path d="M14.5 24.5 L21.5 31.5 L34 17.5" fill="none" stroke={accent} strokeWidth={4.5} strokeLinecap="round" strokeLinejoin="round" {...trim(check)} />
						</svg>
						<div style={{flex: 1, fontSize: size, fontWeight: 500, lineHeight: 1.2, letterSpacing: '-0.015em', color: isDone ? C.ink : C.muted}}>
							<Rise p={rise(start + 2, dur.base)}>{item}</Rise>
						</div>
					</div>
				);
			})}
		</div>
	);
};
