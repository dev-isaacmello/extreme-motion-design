import React from 'react';
import {ThreeCanvas} from '@remotion/three';
import {useVideoConfig} from 'remotion';
import {ease, easeX, keys, timeRemap, tween} from '../lib/motion';
import {useScene} from '../lib/score';
import {C} from '../theme';

/**
 * Cena 5: quatro sólidos que começam como recortes chapados (luz só ambiente, de frente) e ganham
 * volume quando a voz diz "três": a luz acende, o grupo gira e a câmera sobe em órbita.
 */
export const Shapes3D: React.FC = () => {
	const {frame, len, at} = useScene('tresd');
	const {width, height} = useVideoConfig();
	const out = tween(frame, len - 7, 7, 0, 1, ease.exit);
	const depth = tween(frame, at('tres') - 1, 16, 0, 1, ease.move);
	// Rampa de velocidade: dispara no "três", freia para ler e volta ao passo normal.
	const t = timeRemap(Math.max(0, frame - at('tres')), [
		[0, 4.5],
		[14, 0.5],
		[60, 1],
	]);
	const spin = t * 0.035;
	const item = (cue: number, i: number) => tween(frame, cue + i * 3, 10, 0, 1, easeX.overshoot) * (1 - out);
	const cor = at('cor');
	const forma = at('forma');
	// No "forma" cada sólido troca de proporção: o mesmo objeto, outra silhueta.
	const stretch = keys(frame, [forma - 1, forma + 9], [0, 1], [ease.move]);
	const solids: Array<{p: [number, number, number]; c: string; s: number; g: React.ReactNode; sx: number; sy: number}> = [
		{p: [-1.7, 0.75, 0], c: C.accent, s: item(cor, 0), g: <torusKnotGeometry args={[0.62, 0.22, 140, 20]} />, sx: 1, sy: 1 + 0.25 * stretch},
		{p: [1.75, 0.9, 0.3], c: C.second, s: item(cor, 1), g: <icosahedronGeometry args={[0.92, 0]} />, sx: 1 - 0.25 * stretch, sy: 1 + 0.3 * stretch},
		{p: [-0.7, -1.0, 0.5], c: C.pink, s: item(cor, 2), g: <coneGeometry args={[0.82, 1.6, 5]} />, sx: 1 + 0.3 * stretch, sy: 1 - 0.2 * stretch},
		{p: [1.4, -1.15, -0.2], c: C.lime, s: item(cor, 3), g: <sphereGeometry args={[0.72, 40, 28]} />, sx: 1 + 0.35 * stretch, sy: 1 - 0.35 * stretch},
	];
	return (
		<ThreeCanvas width={width} height={height} camera={{fov: 30, position: [0, 0, 13]}} style={{position: 'absolute', inset: 0}}>
			<ambientLight intensity={3.1 - depth * 1.9} />
			<directionalLight position={[4, 6, 5]} intensity={depth * 3.4} />
			<directionalLight position={[-5, -2, 3]} intensity={depth * 0.9} color={C.ink} />
			{/* A câmera fica parada (a prop não reage por frame): quem orbita e se aproxima é o grupo. */}
			<group rotation={[depth * 0.36, spin, depth * 0.06]} position={[0.15, -2.35, 0]} scale={0.78 + depth * 0.08}>
				{solids.map((o, i) => (
					<mesh key={i} position={o.p} scale={[o.s * o.sx, o.s * o.sy, o.s * o.sx]} rotation={[spin * (1.4 + i * 0.3) + i, spin * (0.8 + i * 0.5), i * 0.7]}>
						{o.g}
						<meshStandardMaterial color={o.c} roughness={0.42} metalness={0.05} flatShading={i === 1 || i === 2} />
					</mesh>
				))}
			</group>
		</ThreeCanvas>
	);
};
