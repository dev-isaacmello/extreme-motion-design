import React from 'react';
import {useFormat} from '../lib/format';
import {ease, easeX, tween} from '../lib/motion';
import {C, FONT, MONO, type} from '../theme';
import {BlockTiming, Rise, useBlock} from './shared';

/**
 * Logo sting em quatro fases dentro de `length`: construção (a linha se desenha, 45%), resolução (a marca
 * sobe de trás da linha, que recolhe para um sublinhado), hold e assinatura (80%). Ponha o impacto do
 * áudio no frame `at + length * 0.45`.
 */
export const LogoSting: React.FC<
	BlockTiming & {
		/** Marca em texto. Para logo em SVG ou imagem, passe como filho. */
		text?: string;
		children?: React.ReactNode;
		tagline?: string;
		/** Duração das quatro fases, em frames. */
		length?: number;
		size?: number;
		color?: string;
		accent?: string;
	}
> = ({text, children, tagline, length = 72, size = type.hero, color = C.ink, accent = C.accent, at = 0, out}) => {
	const {u} = useFormat();
	const {frame, rise, k} = useBlock(at, out);
	const len = length / k;
	const build = len * 0.45;
	const resolve = Math.max(12, len * 0.15);
	const line = rise(0, build, ease.move) * tween(frame, build, resolve + 6, 1, 0.16, ease.move);
	return (
		<div style={{display: 'inline-block', fontFamily: FONT}}>
			<Rise p={rise(build, resolve, easeX.emphasized)}>
				<div style={{fontSize: size * u, fontWeight: 800, lineHeight: 1.08, letterSpacing: '-0.045em', color, whiteSpace: 'nowrap'}}>{children ?? text}</div>
			</Rise>
			<div style={{height: 6 * u, marginTop: 16 * u, borderRadius: 3 * u, background: accent, transform: `scaleX(${line})`, transformOrigin: 'left center'}} />
			{tagline ? (
				<div style={{marginTop: 24 * u, fontFamily: MONO, fontSize: 28 * u, lineHeight: 1.3, letterSpacing: '0.14em', textTransform: 'uppercase', color: C.muted, whiteSpace: 'nowrap'}}>
					<Rise p={rise(len * 0.8, 12, ease.sharp)}>{tagline}</Rise>
				</div>
			) : null}
		</div>
	);
};
