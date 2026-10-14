import React from 'react';
import {useFormat} from '../lib/format';
import {dur, ease} from '../lib/motion';
import {C, FONT, type} from '../theme';
import {BlockTiming, Rise, useBlock, wrap} from './shared';

/** Citação tipográfica: aspas no acento, texto revelado linha a linha, depois o autor. */
export const QuoteCard: React.FC<
	BlockTiming & {
		/** Texto corrido (quebrado em `maxChars`) ou as linhas já prontas. */
		quote: string | string[];
		author?: string;
		role?: string;
		width?: number;
		maxChars?: number;
		fontSize?: number;
		accent?: string;
	}
> = ({quote, author, role, width, maxChars, fontSize = type.lead, accent = C.accent, at = 0, out}) => {
	const {u, text, vertical} = useFormat();
	const {rise} = useBlock(at, out);
	const w = width ?? text.w;
	const per = maxChars ?? (vertical ? 22 : 30);
	const lines = Array.isArray(quote) ? quote : wrap(quote, per);
	const longest = Math.max(per, ...lines.map((l) => l.length));
	// Inter em peso 500 ocupa perto de 0,53 em por caractere: a linha mais longa nunca passa da largura.
	const size = Math.min(fontSize * u, w / (longest * 0.53));
	const after = 4 + lines.length * 3;
	return (
		<div style={{width: w, fontFamily: FONT}}>
			<div style={{width: size * 1.5, marginBottom: size * 0.5}}>
				<Rise p={rise(0, dur.base)}>
					<svg viewBox="0 0 110 84" width="100%" style={{display: 'block'}}>
						{[0, 62].map((x) => (
							<path key={x} transform={`translate(${x} 0)`} d="M0 58 C0 26 18 6 44 0 L48 12 C35 17 27 27 26 38 L48 38 L48 84 L0 84 Z" fill={accent} />
						))}
					</svg>
				</Rise>
			</div>
			<div style={{fontSize: size, fontWeight: 500, lineHeight: 1.24, letterSpacing: '-0.022em', color: C.ink, whiteSpace: 'nowrap'}}>
				{lines.map((l, i) => (
					<Rise key={i} p={rise(4 + i * 3, dur.base)}>
						{l}
					</Rise>
				))}
			</div>
			{author ? (
				<div style={{marginTop: size * 0.75, display: 'flex', alignItems: 'center', gap: 20 * u}}>
					<div style={{width: 44 * u, height: 3 * u, background: C.muted, transform: `scaleX(${rise(after + 6, dur.fast, ease.sharp)})`, transformOrigin: 'left center'}} />
					<div style={{fontSize: type.label * 1.1 * u, lineHeight: 1.25, whiteSpace: 'nowrap'}}>
						<Rise p={rise(after + 8, dur.base)}>
							<span style={{fontWeight: 700, color: C.ink}}>{author}</span>
							{role ? <span style={{marginLeft: '0.7em', fontWeight: 500, color: C.muted}}>{role}</span> : null}
						</Rise>
					</div>
				</div>
			) : null}
		</div>
	);
};
