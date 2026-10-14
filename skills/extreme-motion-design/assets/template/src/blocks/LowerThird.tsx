import React from 'react';
import {AbsoluteFill} from 'remotion';
import {useFormat} from '../lib/format';
import {dur, ease} from '../lib/motion';
import {C, FONT} from '../theme';
import {BlockTiming, Rise, alpha, useBlock} from './shared';

/** Identificação de quem fala: barra de acento cresce, nome e cargo sobem por máscara. Fica no canto da área segura. */
export const LowerThird: React.FC<
	BlockTiming & {
		name: string;
		role?: string;
		side?: 'left' | 'right';
		/** Placa escura atrás do texto, para usar sobre vídeo ou imagem clara. */
		plate?: boolean;
		accent?: string;
	}
> = ({name, role, side = 'left', plate = false, accent = C.accent, at = 0, out}) => {
	const {u, text, width, height} = useFormat();
	const {rise} = useBlock(at, out);
	const right = side === 'right';
	const pad = plate ? 22 * u : 0;
	return (
		<AbsoluteFill style={{pointerEvents: 'none', fontFamily: FONT}}>
			<div
				style={{
					position: 'absolute',
					...(right ? {right: width - text.x - text.w} : {left: text.x}),
					bottom: height - text.y - text.h,
					maxWidth: text.w,
					display: 'flex',
					flexDirection: right ? 'row-reverse' : 'row',
					alignItems: 'stretch',
					gap: 22 * u,
					textAlign: right ? 'right' : 'left',
				}}
			>
				<div
					style={{
						width: 6 * u,
						borderRadius: 3 * u,
						background: accent,
						transform: `scaleY(${rise(0, dur.fast, ease.sharp)})`,
						transformOrigin: 'center bottom',
					}}
				/>
				<div style={{position: 'relative', padding: `${pad * 0.6}px ${pad}px`}}>
					{plate ? (
						<div
							style={{
								position: 'absolute',
								inset: 0,
								borderRadius: 8 * u,
								background: alpha(C.bg, 0.82),
								transform: `scaleX(${rise(1, dur.base)})`,
								transformOrigin: right ? 'right center' : 'left center',
							}}
						/>
					) : null}
					<div style={{position: 'relative'}}>
						<div style={{fontSize: 56 * u, fontWeight: 700, lineHeight: 1.12, letterSpacing: '-0.025em', color: C.ink, whiteSpace: 'nowrap'}}>
							<Rise p={rise(4, dur.base)}>{name}</Rise>
						</div>
						{role ? (
							<div style={{marginTop: 6 * u, fontSize: 32 * u, fontWeight: 500, lineHeight: 1.2, color: C.muted, whiteSpace: 'nowrap'}}>
								<Rise p={rise(7, dur.base)}>{role}</Rise>
							</div>
						) : null}
					</div>
				</div>
			</div>
		</AbsoluteFill>
	);
};
