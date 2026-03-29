/* ===========================
   <site-header>
   =========================== */
class SiteHeader extends HTMLElement {
  connectedCallback() {
    const current = this.getAttribute("current") || "";
    this.innerHTML = `
      <header class="site-header">
        <div class="container">
          <a href="/" class="brand">
            <svg width="22" height="26" viewBox="0 0 46 50" fill="none">
              <line x1="6" y1="11" x2="40" y2="11" stroke="#378ADD" stroke-width="4" stroke-linecap="round"/>
              <line x1="23" y1="11" x2="23" y2="31" stroke="#378ADD" stroke-width="4" stroke-linecap="round"/>
              <line x1="23" y1="31" x2="10" y2="46" stroke="#185FA5" stroke-width="3.5" stroke-linecap="round"/>
              <line x1="23" y1="31" x2="36" y2="46" stroke="#85B7EB" stroke-width="3.5" stroke-linecap="round"/>
              <circle cx="10" cy="46" r="2.5" fill="#185FA5"/>
              <circle cx="36" cy="46" r="2.5" fill="#85B7EB"/>
            </svg>
            <span><span class="brand-bold">theo</span><span class="brand-light">lternative</span></span>
          </a>
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
          <div>
            <div class="footer-brand">
              <svg width="18" height="21" viewBox="0 0 46 50" fill="none">
                <line x1="6" y1="11" x2="40" y2="11" stroke="#378ADD" stroke-width="4" stroke-linecap="round"/>
                <line x1="23" y1="11" x2="23" y2="31" stroke="#378ADD" stroke-width="4" stroke-linecap="round"/>
                <line x1="23" y1="31" x2="10" y2="46" stroke="#185FA5" stroke-width="3.5" stroke-linecap="round"/>
                <line x1="23" y1="31" x2="36" y2="46" stroke="#85B7EB" stroke-width="3.5" stroke-linecap="round"/>
              </svg>
              <span><span class="footer-brand-bold">theo</span><span class="footer-brand-light">lternative</span></span>
            </div>
            <span class="copyright">&copy; ${year} theolternative. All rights reserved.</span>
          </div>
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
