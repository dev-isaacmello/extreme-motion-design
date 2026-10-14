import React from 'react';
import {useFormat} from '../lib/format';
import {cascade, dur, ease, pop, springs} from '../lib/motion';
import {C, FONT, MONO, type} from '../theme';
import {BlockTiming, Rise, mix, useBlock} from './shared';

export type Step = {title: string; detail?: string};

/** Linha do tempo de 3 a 5 passos. O trilho se desenha, os nós entram em cascata e o acento avança até o passo ativo. */
export const Steps: React.FC<
	BlockTiming & {
		steps: Step[];
		/** Índice do passo ativo (0 é o primeiro). */
		active?: number;
		/** Padrão: linha em 16:9 e 1:1, coluna em 9:16. */
		direction?: 'row' | 'column';
		width?: number;
		accent?: string;
	}
> = ({steps, active = 0, direction, width, accent = C.accent, at = 0, out}) => {
	const {u, text, vertical} = useFormat();
	const {frame, rise, exit} = useBlock(at, out);
	const n = steps.length;
	const row = (direction ?? (vertical ? 'column' : 'row')) === 'row';
	const w = width ?? text.w;
	const node = 60 * u;
	const cell = row ? w / n : 170 * u;
	const span = (n - 1) * cell;
	const goFrom = 26;
	const goLen = 8 + 4 * active;
	const go = rise(goFrom, goLen, ease.move);
	const lit = Math.min(pop(frame, 30, goFrom + goLen - 3, springs.snappy), 1.2) * (1 - exit);
	const rail: React.CSSProperties = row
		? {left: node / 2, top: node / 2 - 1.5 * u, width: span, height: 3 * u, transformOrigin: 'left center'}
		: {left: node / 2 - 1.5 * u, top: node / 2, width: 3 * u, height: span, transformOrigin: 'center top'};
	const grow = (p: number) => (row ? `scaleX(${p})` : `scaleY(${p})`);
	return (
		<div style={{position: 'relative', width: w, display: 'flex', flexDirection: row ? 'row' : 'column', fontFamily: FONT}}>
			<div style={{position: 'absolute', ...rail, background: C.line, transform: grow(rise(0, dur.base))}} />
			<div style={{position: 'absolute', ...rail, background: accent, transform: grow((go * active) / Math.max(1, n - 1))}} />
			{steps.map((s, i) => {
				const start = 4 + cascade(i, n, 12);
				const isActive = i === active;
				const done = i < active;
				const on = isActive && lit > 0.2;
				return (
					<div
						key={i}
						style={{
							position: 'relative',
							width: row ? cell : '100%',
							minHeight: row ? undefined : i < n - 1 ? cell : node,
							boxSizing: 'border-box',
							display: 'flex',
							flexDirection: row ? 'column' : 'row',
							gap: row ? 26 * u : 30 * u,
							paddingRight: row ? 28 * u : 0,
						}}
					>
						<div style={{position: 'relative', width: node, height: node, flexShrink: 0, transform: `scale(${rise(start, dur.base)})`}}>
							<div
								style={{
									position: 'absolute',
									inset: 0,
									borderRadius: node,
									boxSizing: 'border-box',
									background: done ? mix(C.ink, C.bg, 0.2) : C.bg,
									border: `${3 * u}px solid ${done ? mix(C.ink, C.bg, 0.2) : C.line}`,
								}}
							/>
							{isActive ? <div style={{position: 'absolute', inset: 0, borderRadius: node, background: accent, transform: `scale(${lit})`}} /> : null}
							<div
								style={{
									position: 'absolute',
									inset: 0,
									display: 'flex',
									alignItems: 'center',
									justifyContent: 'center',
									fontFamily: MONO,
									fontSize: 30 * u,
									fontWeight: 700,
									color: on ? C.bg : done ? C.ink : C.muted,
								}}
							>
								{i + 1}
							</div>
						</div>
						<div style={{flex: 1, minWidth: 0, paddingTop: row ? 0 : 6 * u}}>
							<div
								style={{
									fontSize: (row ? 38 : type.body) * u,
									fontWeight: isActive ? 700 : 500,
									lineHeight: 1.15,
									letterSpacing: '-0.02em',
									color: isActive || done ? C.ink : C.muted,
								}}
							>
								<Rise p={rise(start + 3, dur.base)}>{s.title}</Rise>
							</div>
							{s.detail ? (
								<div style={{marginTop: 8 * u, fontSize: type.label * u * (row ? 0.93 : 1), fontWeight: 400, lineHeight: 1.3, color: C.muted}}>
									<Rise p={rise(start + 6, dur.base)}>{s.detail}</Rise>
								</div>
							) : null}
						</div>
					</div>
				);
			})}
		</div>
	);
};
