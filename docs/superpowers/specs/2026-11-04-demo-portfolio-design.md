# Demo portfolio design

The user requests a DevPortfolio / Astro / Tailwind navigation redesign and the first three approved content batches. This is an expansion of the existing public TechYan/demo site. The existing checkout is dedicated to this project.

## Experience

Use RyanFitzgerald/devportfolio as the MIT-licensed Astro/Tailwind foundation. Adapt its developer portfolio information hierarchy into a project catalog: persistent identity/navigation, large editorial introduction, one featured project, a searchable and category-filtered project grid, and seven project detail pages. Use near-black surfaces, fine borders, lime accents, technical mono labels, and readable Chinese descriptions. Project illustrations are small code-native diagrams representing actual functionality. Responsive navigation and reduced-motion support are required.

## Content

Preserve all existing PVKit artifact URLs. Add bus-protocol-lab's three tools; pg_gen's standalone app with fictional register examples; a real UVM Wiki generated from its sanitized demo_uvm fixture; selected SVIP usage/architecture guides and owned examples; xpggen previews and real exporter outputs; xDCT's existing before/after manifests and change report with a browser comparison. No real internal register catalogs, vendor VIP source, credentials, simulator runtimes, or private DUT sources are included. Private source repositories retain their visibility.

## Build and publication

Astro statically renders the navigation. Existing package folders remain the source of the demo artifacts and are copied into dist by an allowlisted build step. GitHub Pages builds with base /demo; Cloudflare Pages builds at /. Internal navigation uses Astro BASE_URL; artifact-relative paths remain portable. GitHub Actions builds and deploys to Pages after validation. Cloudflare Pages uses npm run build with dist output, and can be connected to the same GitHub repository or deployed through Wrangler with an already authorized account. No new account or credentials are created by the implementation.

## Verification

Test search/filter semantics, both deployment bases, generated detail routes, every static local link, artifact completeness, absence of source-only private material, and preserved PVKit checksums. Use browser checks for catalog filters/search, keyboard navigation, mobile overflow, representative tools and report views. Verify the public deployment and report Cloudflare authentication requirements accurately if no authorized account is available.
