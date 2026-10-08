import React, {createContext, useContext} from 'react';
import {AbsoluteFill} from 'remotion';

type Cam = {x: number; y: number; zoom: number; rotate: number};
const CamCtx = createContext<Cam>({x: 0, y: 0, zoom: 1, rotate: 0});

/**
 * Câmera 2.5D. x e y em px do mundo, zoom 1 = enquadramento base, rotate em graus.
 * Zoom in, zoom out, push-in, pan, whip pan e câmera na mão saem daqui.
 */
export const Camera: React.FC<Partial<Cam> & {children: React.ReactNode}> = ({
	x = 0,
	y = 0,
	zoom = 1,
	rotate = 0,
	children,
}) => (
	<CamCtx.Provider value={{x, y, zoom, rotate}}>
		<AbsoluteFill style={{overflow: 'hidden'}}>{children}</AbsoluteFill>
	</CamCtx.Provider>
);

/**
 * Camada com profundidade. depth 1 = plano focal; maior que 1 fica longe e se move menos;
 * menor que 1 fica perto e se move mais. É isso que cria o parallax.
 */
export const Layer: React.FC<{depth?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({
	depth = 1,
	children,
	style,
}) => {
	const {x, y, zoom, rotate} = useContext(CamCtx);
	const k = 1 / depth;
	const z = 1 + (zoom - 1) * k;
	return (
		<AbsoluteFill
			style={{
				transform: `scale(${z}) rotate(${rotate * k}deg) translate(${-x * k}px, ${-y * k}px)`,
				transformOrigin: '50% 50%',
				...style,
			}}
		>
			{children}
		</AbsoluteFill>
	);
};
