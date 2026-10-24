# design_system

Shared visual language for the web app, the Remotion video and the documentation. Light by default, dark on a switch, in all three.

| File | What it is |
|---|---|
| `DESIGN_SYSTEM.md` | The spec: principles, color, type, space, components, voice, video, accessibility |
| `IMAGERY.md` | Image sources, page by page ideas, licence rules |
| `tokens/tokens.json` | Source of truth. Edit values here only |
| `scripts/build.mjs` | Generates the files below. `node design_system/scripts/build.mjs`, no install needed |
| `dist/tokens.css` | CSS variables (`--rs-*`), light, dark and `prefers-color-scheme`, plus `.rs-text-*` classes |
| `dist/tokens.ts` | Typed constants for the web app and Remotion |
| `dist/preview.html` | Open in a browser to see palette, type, buttons, toasts, tiles and hero flow chips, with a theme switch |
| `assets/CREDITS.md` | Create when the first image is added: file, source, author, licence |

## Use it

* **Web**: `import 'design_system/dist/tokens.css'`, then `var(--rs-action-primary)` and `.rs-text-kpi-hero`. Map the same tokens into the CSS or Tailwind setup chosen in week 1.
* **Remotion**: `import { tokens } from '../design_system/dist/tokens'`, then `tokens.video.theme[mode]` and `tokens.semantic[mode]`. Default mode is `light`.
* **Docs**: link `tokens.css` in any generated HTML.

After editing `tokens.json`, rebuild and commit `dist/` with it. Add a CI step that rebuilds and fails on a diff once CI exists.
