/* ===========================
   <site-header>
   =========================== */
class SiteHeader extends HTMLElement {
  connectedCallback() {
    const current = this.getAttribute("current") || "";
    this.innerHTML = `
      <header class="site-header">
        <div class="container">
          <a href="/" class="brand">theolternative</a>
          <nav>
            <a href="/"${current === "home" ? ' aria-current="page"' : ""}>Home</a>
            <a href="/about/"${current === "about" ? ' aria-current="page"' : ""}>About</a>
          </nav>
        </div>
      </header>
    `;
  }
}
customElements.define("site-header", SiteHeader);

/* ===========================
   <site-footer>
   =========================== */
class SiteFooter extends HTMLElement {
  connectedCallback() {
    const year = new Date().getFullYear();
    this.innerHTML = `
      <footer class="site-footer">
        <div class="container">
          <span class="copyright">&copy; ${year} theolternative. All rights reserved.</span>
          <nav>
            <a href="/">Home</a>
            <a href="/about/">About</a>
            <a href="/support/">Support</a>
            <a href="/privacy/">Privacy</a>
          </nav>
        </div>
      </footer>
    `;
  }
}
customElements.define("site-footer", SiteFooter);

/* ===========================
   <app-card>
   Attributes: name, slug, description, icon, screenshot, store-url
   =========================== */
class AppCard extends HTMLElement {
  connectedCallback() {
    const name = this.getAttribute("name") || "App";
    const slug = this.getAttribute("slug") || "";
    const description = this.getAttribute("description") || "";
    const icon = this.getAttribute("icon") || "";
    const screenshot = this.getAttribute("screenshot") || "";
    const storeUrl = this.getAttribute("store-url") || "#";

    const iconHTML = icon
      ? `<img src="${icon}" alt="${name} icon">`
      : "";

    const screenshotHTML = screenshot
      ? `<div class="app-card-screenshot"><img src="${screenshot}" alt="${name} screenshot"></div>`
      : "";

    this.innerHTML = `
      <div class="app-card">
        <div class="app-card-top">
          <div class="app-card-icon">${iconHTML}</div>
          <div class="app-card-info">
            <h3>${name}</h3>
          </div>
        </div>
        <p class="app-card-description">${description}</p>
        ${screenshotHTML}
        <div class="app-card-actions">
          <a href="/apps/${slug}/" class="btn-learn-more">Learn more</a>
          <a href="${storeUrl}" target="_blank" rel="noopener">
            <img class="app-store-badge"
                 src="https://tools.applemediaservices.com/api/badges/download-on-the-app-store/black/en-us?size=250x83"
                 alt="Download on the App Store">
          </a>
        </div>
      </div>
    `;
  }
}
customElements.define("app-card", AppCard);
