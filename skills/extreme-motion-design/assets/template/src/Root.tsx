import React from 'react';
import {Composition} from 'remotion';
import timeline from '../public/timeline.json';
import {Showcase} from './scenes/Showcase';

// timeline.json é a partitura: duração, cenas, narração, trilha, SFX e loudness.
// Vídeo (este arquivo), mixagem (scripts/mix.py) e QA (scripts/qa.py) leem o mesmo arquivo.
export const RemotionRoot: React.FC = () => (
	<Composition
		id="Showcase"
		component={Showcase}
		durationInFrames={Math.round(timeline.duration * timeline.fps)}
		fps={timeline.fps}
		width={timeline.width}
		height={timeline.height}
	/>
);
