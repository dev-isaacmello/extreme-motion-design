import {loadFont as loadDisplay} from '@remotion/google-fonts/Inter';
import {loadFont as loadMono} from '@remotion/google-fonts/JetBrainsMono';
import brand from '../public/brand.json';

// Marca do vídeo. As cores vêm de public/brand.json (scripts/brand.py extrai de um site ou repositório).
// Cena nenhuma escreve hex solto: use C.*. O lint avisa cor fora daqui.
// Para trocar a fonte, troque os dois imports acima pela família da marca em @remotion/google-fonts
// (ou carregue um arquivo local com @remotion/fonts) e mantenha brand.json com o mesmo nome.
const display = loadDisplay('normal', {weights: ['400', '500', '700', '800'], subsets: ['latin']});
const mono = loadMono('normal', {weights: ['400', '700'], subsets: ['latin']});

export const C = brand.colors;
export const BRAND = brand;
export const FONT = `${display.fontFamily}, "Helvetica Neue", Arial, sans-serif`;
export const MONO = `${mono.fontFamily}, Menlo, monospace`;

/** Escala tipográfica em px para o lado menor de 1080; multiplique por `u` de useFormat(). */
export const type = {hero: 148, title: 96, lead: 64, body: 44, label: 30};
