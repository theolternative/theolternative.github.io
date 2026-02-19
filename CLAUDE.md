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
* `images/screenshots/<slug>/` — App Store screenshots (iPhone and iPad)
* `sitemap.xml` — Sitemap for search engines
* `robots.txt` — Crawler directives
* `site.webmanifest` — Web app manifest with icon references
* `CNAME` — GitHub Pages custom domain

## Conventions
* Light theme (default): background `#ffffff`, accent `#0071e3`
* Per-app themes via `data-theme` on `<body>` — overrides CSS custom properties
  * `steel-dark`: dark background `#1a1a1e`, golden accent `#e5a51b` (matches Steel Profiles app icons)
  * `livesick-dark`: dark background `#1a1a1e`, amber accent `#e8a520` (matches Livesick app icon)
* Reusable Web Components for header, footer, and app cards
* Responsive: mobile-first, grid switches at 640px breakpoint
* All internal links use absolute paths (e.g. `/apps/steel-profiles-aisc/`)
* App Store badge loaded from Apple Media Services CDN (black on light pages, white on dark pages)
* Page titles follow the pattern: `Page Name — theolternative`
* All pages include: favicon, apple-touch-icon, OG tags, Twitter Cards, canonical URL, theme-color, manifest link
* `meta theme-color` matches the page theme (`#ffffff` light, `#1a1a1e` dark)
* Footer includes links to Home, About, Support, and Privacy

## Current Apps
* **Livesick** — slug: `livesick`, App Store ID: `id1635028224`
* **Steel Profiles AISC** — slug: `steel-profiles-aisc`, App Store ID: `id662511256`
* **Steel Profiles Free** — slug: `steel-profiles-free`, App Store ID: `id564614324`
