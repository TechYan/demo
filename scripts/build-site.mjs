import { cpSync, existsSync, readFileSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const github = process.argv.includes('--github');
const astroPackage = new URL('../node_modules/astro/package.json', import.meta.url);
const astroBin = new URL(JSON.parse(readFileSync(astroPackage, 'utf8')).bin.astro, astroPackage);
const result = spawnSync(process.execPath, [fileURLToPath(astroBin), 'build'], {
  cwd: root,
  stdio: 'inherit',
  env: { ...process.env, SITE_BASE: github ? '/demo/' : '/', ...(github ? { SITE_URL: 'https://techyan.github.io' } : {}) },
});
if (result.status !== 0) process.exit(result.status || 1);

const packages = ['assets', 'pvkit', 'bus-protocol-lab', 'pg_gen', 'uvm_wiki', 'svip', 'xpggen', 'xDCT'];
for (const directory of packages) {
  if (!existsSync(new URL(`../${directory}/`, import.meta.url))) throw new Error(`Missing demo package: ${directory}`);
  cpSync(new URL(`../${directory}/`, import.meta.url), new URL(`../dist/${directory}/`, import.meta.url), { recursive: true });
}
writeFileSync(new URL('../dist/.nojekyll', import.meta.url), '');
console.log(`Copied ${packages.length - 1} demo packages; deployment base: ${github ? '/demo/' : '/'}`);
