/**
 * Patch @wxperia/liquid-glass-vue to fix Vite/Rollup build error.
 * The package uses `new URL("/assets/shader-worker-CJN-6C3l.js", import.meta.url)`
 * which Rollup's commonjs resolver can't handle. We patch it to use a plain string URL
 * and serve the shader worker from the public/assets/ directory.
 */
import { readFileSync, writeFileSync, copyFileSync, mkdirSync, existsSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const distDir = resolve(__dirname, '../node_modules/@wxperia/liquid-glass-vue/dist')

// Patch ESM
const esmPath = resolve(distDir, 'index.js')
if (existsSync(esmPath)) {
  let esm = readFileSync(esmPath, 'utf8')
  esm = esm.replace(
    /this\.worker\s*=\s*new Worker\(new URL\(\s*\/\*\s*@vite-ignore\s*\*\/\s*"[^"]*shader-worker[^"]*",\s*import\.meta\.url\s*\),\s*\{\s*type:\s*"module"\s*\}\);?/,
    'this.worker = new Worker("/assets/shader-worker-CJN-6C3l.js", { type: "module" });'
  )
  writeFileSync(esmPath, esm)
}

// Patch CJS
const cjsPath = resolve(distDir, 'index.cjs')
if (existsSync(cjsPath)) {
  let cjs = readFileSync(cjsPath, 'utf8')
  cjs = cjs.replace(
    /this\.worker\s*=\s*new Worker\(new URL\(\s*\/\*\s*@vite-ignore\s*\*\/\s*"[^"]*shader-worker[^"]*",[^)]*\),\s*\{\s*type:\s*"module"\s*\}\);?/,
    'this.worker = new Worker("/assets/shader-worker-CJN-6C3l.js", { type: "module" });'
  )
  writeFileSync(cjsPath, cjs)
}

// Copy shader worker to public/assets/
const workerSrc = resolve(distDir, 'assets/shader-worker-CJN-6C3l.js')
const publicDir = resolve(__dirname, '../public/assets')
if (existsSync(workerSrc)) {
  mkdirSync(publicDir, { recursive: true })
  copyFileSync(workerSrc, resolve(publicDir, 'shader-worker-CJN-6C3l.js'))
}

console.log('✓ Patched @wxperia/liquid-glass-vue for Vite compatibility')
