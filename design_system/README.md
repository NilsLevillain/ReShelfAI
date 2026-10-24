# design_system

Shared visual language for the web app, the Remotion video, the documentation and feature pages such as the product management recap. Light by default, dark on a switch, in all of them.

| File | What it is |
|---|---|
| `DESIGN_SYSTEM.md` | The spec: principles, color, type, space, components, voice, video, accessibility, logo, icons, responsive layout |
| `IMAGERY.md` | Image sources, page by page ideas, licence rules |
| `tokens/tokens.json` | Source of truth for values. Edit values here only |
| `components/components.css` | Hand written components and page layout, tokens only, `rs-` prefix |
| `assets/icons.json` | Icon set (24 grid, 2 px stroke) |
| `assets/logo/` | Mark in color and mono |
| `assets/illustrations/flow-hero.svg` | The animated hero storytelling asset |
| `scripts/build.mjs` | Generates everything below. `node design_system/scripts/build.mjs`, no install needed |
| `dist/tokens.css` | CSS variables (`--rs-*`), light, dark and `prefers-color-scheme`, plus `.rs-text-*` classes |
| `dist/components.css` | Copy of `components/components.css` for apps and pages |
| `dist/icons.svg`, `dist/icons.ts` | Icon sprite and typed icon map |
| `dist/tokens.ts` | Typed constants for the web app and Remotion |
| `dist/preview.html` | Open in a browser to see palette, type, buttons, toasts, tiles, hero flow chips, logo, icons and card hover, with a theme switch |
| `assets/CREDITS.md` | Create when the first image is added: file, source, author, licence |

## Use it

* **Web**: `import 'design_system/dist/tokens.css'` then `'design_system/dist/components.css'`. Inline `dist/icons.svg` once and use `<svg class="rs-icon"><use href="#rs-i-euro"/></svg>`.
* **Remotion**: `import { tokens } from '../design_system/dist/tokens'`, then `tokens.video.theme[mode]` and `tokens.semantic[mode]`. Default mode is `light`.
* **Docs and feature pages**: link `tokens.css` and `components.css`. The recap page is the reference: `product_management/recap.src.html` is the source, and the build writes `product_management/recap.html` with everything inlined so it works on its own.

After editing `tokens.json`, `components.css`, `icons.json` or the recap source, rebuild and commit `dist/` and `recap.html` with it. Add a CI step that rebuilds and fails on a diff once CI exists.
