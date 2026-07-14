import typescript from '@rollup/plugin-typescript';
import { nodeResolve } from '@rollup/plugin-node-resolve';
import terser from '@rollup/plugin-terser';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const ENTRY = path.resolve(__dirname, 'src/little-buddy-card.ts');
const OUT = path.resolve(
  __dirname,
  'custom_components/little_buddy_card/frontend/little-buddy-card.js',
);

export default {
  input: ENTRY,
  output: {
    file: OUT,
    format: 'es',
  },
  plugins: [
    nodeResolve(),
    typescript({
      tsconfig: path.resolve(__dirname, 'tsconfig.json'),
      compilerOptions: { target: 'ES2022' },
    }),
    terser({ ecma: 2022 }),
  ],
};
