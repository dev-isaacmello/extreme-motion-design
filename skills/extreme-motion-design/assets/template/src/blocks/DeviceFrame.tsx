import React from 'react';
import {useFormat} from '../lib/format';
import {dur, easeX} from '../lib/motion';
import {C, MONO} from '../theme';
import {BlockTiming, mix, surface, useBlock} from './shared';

/** Moldura de celular ou de janela de browser. Os filhos são a tela: use 100% de largura e altura. */
export const DeviceFrame: React.FC<
	BlockTiming & {
		variant?: 'phone' | 'browser';
		children?: React.ReactNode;
		/** Largura em px reais (já com u). Padrão: cabe na área segura do formato. */
		width?: number;
		/** Endereço mostrado na barra do browser. */
		url?: string;
		/** Altura da tela do browser em relação à largura. */
		ratio?: number;
		screen?: string;
	}
> = ({variant = 'phone', children, width, url = 'exemplo.com.br', ratio = 0.6, screen = mix(C.ink, C.bg, 0.05), at = 0, out}) => {
	const {u, text} = useFormat();
	const {rise} = useBlock(at, out);
	const enter = surface(rise(0, dur.slow, easeX.emphasized), u);
	const edge = mix(C.ink, C.bg, 0.2);
	const shadow = `0 ${36 * u}px ${90 * u}px rgba(0, 0, 0, 0.5)`;

	if (variant === 'browser') {
		const w = width ?? Math.min(text.w, (text.h - 64 * u) / ratio);
		const dot = 14 * u;
		return (
			<div
				style={{
					...enter,
					width: w,
					borderRadius: 20 * u,
					overflow: 'hidden',
					background: mix(C.ink, C.bg, 0.09),
					boxShadow: `${shadow}, inset 0 0 0 ${1.5 * u}px ${edge}`,
				}}
			>
				<div data-decor style={{height: 64 * u, display: 'flex', alignItems: 'center', padding: `0 ${24 * u}px`}}>
					<div style={{display: 'flex', gap: 10 * u, width: 3 * dot + 20 * u}}>
						{[0, 1, 2].map((i) => (
							<div key={i} style={{width: dot, height: dot, borderRadius: dot, background: mix(C.ink, C.bg, 0.26)}} />
						))}
					</div>
					<div
						style={{
							flex: 1,
							maxWidth: w * 0.46,
							margin: '0 auto',
							height: 38 * u,
							borderRadius: 19 * u,
							background: mix(C.ink, C.bg, 0.03),
							display: 'flex',
							alignItems: 'center',
							justifyContent: 'center',
							fontFamily: MONO,
							fontSize: 20 * u,
							color: C.muted,
							whiteSpace: 'nowrap',
							overflow: 'hidden',
						}}
					>
						{url}
					</div>
					<div style={{width: 3 * dot + 20 * u}} />
				</div>
				<div style={{position: 'relative', width: '100%', height: w * ratio, overflow: 'hidden', background: screen}}>{children}</div>
			</div>
		);
	}

	const w = width ?? Math.min(text.w * 0.6, text.h / 2.08);
	return (
		<div
			style={{
				...enter,
				width: w,
				height: w * 2.08,
				padding: w * 0.032,
				boxSizing: 'border-box',
				borderRadius: w * 0.16,
				background: mix(C.ink, C.bg, 0.12),
				boxShadow: `${shadow}, inset 0 0 0 ${1.5 * u}px ${mix(C.ink, C.bg, 0.3)}`,
			}}
		>
			<div style={{position: 'relative', width: '100%', height: '100%', borderRadius: w * 0.13, overflow: 'hidden', background: screen}}>
				{children}
				<div
					style={{
						position: 'absolute',
						top: w * 0.03,
						left: '50%',
						width: w * 0.28,
						height: w * 0.08,
						marginLeft: -w * 0.14,
						borderRadius: w * 0.04,
						background: C.bg,
					}}
				/>
			</div>
		</div>
	);
};
