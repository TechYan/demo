# Demo portfolio implementation plan

> For agentic workers: use the already dispatched independent content agents and inline parent implementation; all share the existing dedicated checkout with disjoint file ownership.

**Goal:** Publish a polished Astro/Tailwind catalog with PVKit and the six authorized projects.

**Architecture:** Astro produces the catalog and project overview routes. An allowlisted copy step preserves standalone artifacts and their URLs. Content packages are isolated by project.

**Tech Stack:** DevPortfolio foundation, Astro 7, Tailwind 4, Node 24, GitHub Pages Actions, Cloudflare Pages static build.

**Spec:** ../specs/2026-11-04-demo-portfolio-design.md

## Global constraints

- Retain all published PVKit artifact URLs and input bytes.
- Add only synthetic/scoped public demo content from authorized repositories.
- Support /demo on GitHub and / on Cloudflare, without per-host manual source edits.
- Never commit credentials, node_modules, cloned source snapshots, or build output.

## Tasks

- [x] Add Node tests for search/filter behavior and subpath-safe navigation; verify the missing implementation fails, then implement src/lib/catalog.mjs.
- [x] Add Astro/Tailwind configuration, package scripts, template attribution and seven-project data in src/data/projects.json. Install pinned lockfile dependencies.
- [x] Build responsive layout/components, catalog, SVG project previews and generated /projects/[id]/ pages. Verify catalog tests and Astro production build.
- [x] Integrate three independent content deliveries (bus/PG, UVM/SVIP, xpggen/xDCT), reviewing manifests and all artifact paths.
- [x] Add allowlisted static copy and static-link/package checks. Build and check both deployment bases, including preserved PVKit checksums.
- [x] Run desktop/mobile browser checks against the built site and representative artifact interactions; fix observed issues.
- [x] Update README/deployment instructions, configure GitHub Pages Actions and Cloudflare Pages build, then publish authorized changes. Verify the returned GitHub deployment and public URLs; finish Cloudflare publication when an authenticated account is available.
