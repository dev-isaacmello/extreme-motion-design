import React from 'react';
import {Composition} from 'remotion';
import timeline from '../public/timeline.json';
import {FORMATS, FormatName} from './lib/format';
import {BLOCKS_DEMO_FRAMES, BlocksDemo} from './scenes/BlocksDemo';
import {Showcase} from './scenes/Showcase';

// timeline.json é a partitura: duração, cenas, narração, trilha, SFX e loudness.
// Vídeo (este arquivo), mixagem (scripts/mix.py), lint e QA leem o mesmo arquivo.
// A prop `format` (reels, square, youtube) troca o tamanho sem trocar de composição: scripts/render.py usa.
type Props = {format: FormatName | null; probe: boolean};
const defaults: Props = {format: null, probe: false};
const sized = ({props}: {props: Record<string, unknown>}) => {
	const f = props.format as FormatName | null;
	return f ? FORMATS[f] : {};
};

export const RemotionRoot: React.FC = () => (
	<>
		<Composition
			id="Showcase"
			component={Showcase}
			durationInFrames={Math.round(timeline.duration * timeline.fps)}
			fps={timeline.fps}
			width={timeline.width}
			height={timeline.height}
			defaultProps={defaults}
			calculateMetadata={sized}
		/>
		<Composition
			id="Blocks"
			component={BlocksDemo}
			durationInFrames={Math.round((BLOCKS_DEMO_FRAMES * timeline.fps) / 30)}
			fps={timeline.fps}
			width={timeline.width}
			height={timeline.height}
			defaultProps={defaults}
			calculateMetadata={sized}
		/>
	</>
);
