Revamp of website www.theolternative.com

## Goals
* Only static assets (HTML, CSS, JS) — no build tools or frameworks
* Served on GitHub Pages (CNAME: theolternative.com)
* Search on AppStore for already published apps and create specific product pages
* No blog

## Structure
* `index.html` — Homepage with hero section and app cards grid
* `about/index.html` — About page
* `apps/<slug>/index.html` — Individual product pages for each app
* `privacy/index.html` — Privacy policy
* `support/index.html` — Support/contact page
* `404.html` — Custom 404 page for GitHub Pages
* `css/style.css` — Single stylesheet using CSS custom properties
* `js/components.js` — Web Components (`<site-header>`, `<site-footer>`, `<app-card>`)
* `images/` — App icons, favicons, and PWA icons
* `images/screenshots/<slug>/` — App Store screenshots (iPhone, iPad and, for Steel Profiles, Mac at 1440×900) in WebP format; `.screenshot-ipad` / `.screenshot-mac` classes size landscape images
* `steel-sections/` — Generated reference pages (do not edit by hand): `index.html`, one index per library (`eu/`, `uk/`), one table page per series (`eu/hea/`) and one page per hot-rolled section (`eu/hea/hea-200/`) with an SVG drawing and the free "Dimensions" group of the app. Hollow sections only get series tables; UK hollow sections are skipped (same EN 10210/10219 data as EU). Regenerate with `python3 tools/generate_steel_sections.py` (reads `tools/data/sections-dimensions.json`, a trimmed export of the app catalog; pass the full `sections.json` export from the app repo as an argument to refresh the trimmed copy). The script also rewrites `sitemap.xml` and the data-driven guide `guides/hea-heb-hem/`
* `guides/<slug>/index.html` — Hand-written reference articles (bolt resistances, W shape designation, steel grade equivalents); `guides/hea-heb-hem/` is generated
* `apps/steel-profiles-free/whats-new/` — Release notes page (not a blog: one page, newest release first)
* Reference-page CSS lives at the end of `css/style.css` (`.crumbs`, `.spec-table`, `.section-figure`, `.series-grid`, `.series-links`, `.cta-card`, `.article`)
* App Store links on EU pages carry `?ppid=65391258-…` (Eurocode custom product page) and on AISC pages `?ppid=c5461109-…` (AISC custom product page); the default page is shown if the custom page is unavailable
* `sitemap.xml` — Sitemap for search engines (rewritten by the generator)
* `robots.txt` — Crawler directives
* `site.webmanifest` — Web app manifest with icon references
* `CNAME` — GitHub Pages custom domain

## Conventions
* Light theme (default): page background `#F0F4FA`, accent `#378ADD`, header/footer transparent
* Per-app themes via `data-theme` on `<body>` — overrides CSS custom properties
  * `steel-dark`: dark background `#1a1a1e`, golden accent `#e5a51b` (matches Steel Profiles app icons)
  * `livesick-dark`: dark background `#1a1a1e`, amber accent `#e8a520` (matches Livesick app icon)
* Reusable Web Components for header, footer, and app cards
* Responsive: mobile-first, grid switches at 640px breakpoint
* All internal links use absolute paths (e.g. `/apps/steel-profiles-aisc/`)
* App Store badge loaded from Apple Media Services CDN (black on light pages, white on dark pages)
* Page titles follow the pattern: `Page Name — theolternative`
* All pages include: favicon, apple-touch-icon, OG tags, Twitter Cards, canonical URL, theme-color, manifest link
* `meta theme-color` is `#F0F4FA` on light pages (matches dark header), `#1a1a1e` on app dark-themed pages
* Footer includes links to Home, About, Support, and Privacy
* Images: use WebP format for screenshots (convert with `cwebp -q 80`); keep PNG only for icons and favicons

## Current Apps
* **Livesick** — slug: `livesick`, App Store ID: `id1635028224`
* **Steel Profiles Pro** (formerly Steel Profiles AISC, renamed Oct 2026) — slug: `steel-profiles-pro`, App Store ID: `id662511256`; `apps/steel-profiles-aisc/` is a meta-refresh redirect to it. Its screenshots are the free app's (`images/screenshots/steel-profiles-free/`): same UI
* **Steel Profiles** (formerly Steel Profiles Free) — slug: `steel-profiles-free`, App Store ID: `id564614324`
* **WiFiPhoto** — slug: `wifiphoto`, App Store ID: `id328578837`
