import typescript from '@rollup/plugin-typescript';
import { nodeResolve } from '@rollup/plugin-node-resolve';
import { terser } from 'rollup-plugin-terser';

export default {
  input: 'src/little-buddy-card.ts',
  output: {
    file: 'dist/little-buddy-card.js',
    format: 'es',
  },
  plugins: [
    nodeResolve(),
    typescript({ compilerOptions: { target: 'ES2022' }, inlineSources: true }),
    terser({ ecma: 2022 })
  ],
};
