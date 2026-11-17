// Design system audit: nothing visual may live only in a page.
//
//   node design_system/scripts/audit.mjs
//
// Checks the web app source (apps/web/src, tests and generated files left out) against the design system:
//   1. every `rs-*` class a page uses is defined in design_system/components/components.css
//   2. no hex color, and no rgb or hsl color other than the transparent one
//   3. no inline style, except `--rs-*` custom properties that carry a data value (a bar share, a dot color token)
//   4. no pixel value in a page
//   5. no amount formatted as currency outside data/currency.tsx (use `useMoney`)
// Exits with 1 and one line per finding. Run in CI, so a page that reinvents a style fails the build.

import { readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const webSrc = join(root, 'apps', 'web', 'src');
const css = readFileSync(join(root, 'design_system', 'components', 'components.css'), 'utf8');

const defined = new Set([...css.matchAll(/\.(rs-[a-z0-9_-]+)/g)].map((m) => m[1]));

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) {
      if (name === 'test' || name === 'api') continue;
      yield* walk(path);
    } else if (/\.(ts|tsx)$/.test(name) && !/\.test\.(ts|tsx)$/.test(name) && !name.endsWith('.d.ts')) {
      yield path;
    }
  }
}

const findings = [];
const add = (file, line, rule, text) => findings.push(`${relative(root, file)}:${line}  ${rule}  ${text.trim().slice(0, 110)}`);

for (const file of walk(webSrc)) {
  const source = readFileSync(file, 'utf8');
  const lines = source.split(/\r?\n/);
  const isCurrency = file.endsWith(join('data', 'currency.tsx'));
  lines.forEach((text, i) => {
    const n = i + 1;
    if (/^\s*(\/\/|\*|\/\*)/.test(text)) return;
    // 1. classes
    // Sprite ids (#rs-i-flag) and custom properties (--rs-share) are not classes.
    for (const m of text.matchAll(/(?<![-\w#])(rs-[a-z0-9_-]+)/g)) {
      if (/^rs-i-?$/.test(m[1])) continue;
      if (!defined.has(m[1])) add(file, n, 'unknown-class', `${m[1]} is not in components.css`);
    }
    // 2. colors
    if (/#[0-9a-fA-F]{3,8}\b/.test(text) && !/&#\d+;/.test(text)) add(file, n, 'hex-color', text);
    for (const m of text.matchAll(/\b(rgba?|hsla?)\(([^)]*)\)/g)) {
      if (m[0].replace(/\s/g, '') !== 'rgba(0,0,0,0)') add(file, n, 'raw-color', m[0]);
    }
    // 3. inline style
    if (/style=\{/.test(text)) {
      const body = text.slice(text.indexOf('style={'));
      // `style={style}` is fine when the file builds that object from `--rs-*` custom properties.
      const viaVariable = /style=\{\w+\}/.test(body) && /['"]--rs-[a-z-]+['"]\s*:/.test(source);
      if (viaVariable) return;
      if (!/['"]--rs-[a-z-]+['"]\s*:/.test(body) || /\b(color|width|height|margin|padding|background|fontSize|display)\s*:/.test(body)) {
        add(file, n, 'inline-style', text);
      }
    }
    // 4. pixels
    if (/\b\d+(\.\d+)?px\b/.test(text)) add(file, n, 'pixel-value', text);
    // 5. currency
    if (!isCurrency && /style:\s*'currency'|toLocaleString\([^)]*currency/.test(text)) {
      add(file, n, 'raw-currency', 'format amounts with useMoney()');
    }
  });
}

if (findings.length) {
  console.error(`Design system audit: ${findings.length} finding(s)\n` + findings.join('\n'));
  process.exit(1);
}
console.log(`Design system audit: clean (${defined.size} classes defined)`);
