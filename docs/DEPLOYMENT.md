# Build and deployment

The same source produces a completely static site for GitHub Pages and Cloudflare Pages. No server-side adapter, database, API keys, or runtime secrets are required by the published site.

## GitHub Pages

The workflow `.github/workflows/pages.yml` runs on pushes to `main` and manual dispatch. It installs the lockfile dependencies, runs the catalog tests, builds with base `/demo/`, checks all local links and PVKit hashes, then uploads and deploys `dist/`.

Repository Settings → Pages → Source must be **GitHub Actions**, replacing the old branch-root publishing mode. Existing artifact paths, such as `/demo/pvkit/examples/axi4/concurrent/traffic.pv.html`, remain valid.

```bash
npm ci
npm test
npm run build:github
python scripts/check_site.py dist /demo
```

## Cloudflare Pages

Target project: **techyan-demo**. Root-path build:

```bash
npm ci
npm run build
npm run check:site
```

For a Cloudflare Pages Git integration, use repository `TechYan/demo`, production branch `main`, build command `npm run build`, output directory `dist`, and Node.js `24`. Leave `SITE_BASE` unset. Cloudflare provides `CF_PAGES_URL` for canonical URL generation.

For an account-authorized direct upload using the project-local Wrangler:

```bash
npx wrangler whoami
npx wrangler pages project list
# Only if the project does not exist:
npx wrangler pages project create techyan-demo --production-branch main
npm run deploy:cloudflare
```

Wrangler authentication is separate from the Codex Cloudflare MCP OAuth login. Its current login supports selected scopes; Pages upload needs account/user discovery and Pages write. Complete OAuth in the official browser flow, and never put the returned token in the repository or chat.

A Direct Upload project supports deployment from local builds or external CI, but cannot be converted in place to Cloudflare's built-in Git integration. Choose Git integration before creating a new project if that is the intended maintenance workflow. External CI can still deploy a Direct Upload project using an account-owned Pages-scoped token stored in the CI secret store.

No account credentials, account IDs, or tokens are embedded in `wrangler.toml` or generated output. `_headers` adds content-type protection and a referrer policy; it deliberately leaves the independent demos' inline scripts intact.

## Artifact verification

```bash
python scripts/check_site.py dist
python scripts/build_uvm_svip.py --check
python scripts/build_register_demos.py --check
```

The static checker validates all HTML local paths, seven project routes, every registered artifact link, 348 PVKit hashes, asset sizes below the Pages 25 MiB single-file limit, and the absence of source-only binaries or internal register catalogs.

Individual rebuild commands are in each package README. A private source checkout is only needed to rebuild the corresponding package, not to build or browse this public site.

## Sources

- [Astro: GitHub Pages](https://docs.astro.build/en/guides/deploy/github/)
- [Cloudflare Pages: Astro](https://developers.cloudflare.com/pages/framework-guides/deploy-an-astro-site/)
- [Cloudflare Pages: Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/)
- [Tailwind: Astro integration](https://tailwindcss.com/docs/installation/framework-guides/astro)
