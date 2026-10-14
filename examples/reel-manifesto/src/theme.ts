import {loadFont as loadDisplay} from '@remotion/google-fonts/Anton';
import {loadFont as loadBody} from '@remotion/google-fonts/Inter';
import {loadFont as loadMono} from '@remotion/google-fonts/JetBrainsMono';
import brand from '../public/brand.json';

// Marca do vídeo: cores de public/brand.json. Anton para o texto gigante, Inter para apoio, JetBrains Mono para código.
const display = loadDisplay('normal', {weights: ['400'], subsets: ['latin', 'latin-ext']});
const body = loadBody('normal', {weights: ['500', '700', '800'], subsets: ['latin', 'latin-ext']});
const mono = loadMono('normal', {weights: ['400', '700'], subsets: ['latin', 'latin-ext']});

export const C = brand.colors;
export const BRAND = brand;
export const DISPLAY = `${display.fontFamily}, Impact, sans-serif`;
export const FONT = `${body.fontFamily}, "Helvetica Neue", Arial, sans-serif`;
export const MONO = `${mono.fontFamily}, Menlo, monospace`;

/** Escala tipográfica em px para o lado menor de 1080; multiplique por `u` de useFormat(). */
export const type = {hero: 148, title: 96, lead: 64, body: 44, label: 30};
