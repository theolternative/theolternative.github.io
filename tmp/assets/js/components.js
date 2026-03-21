const BADGE_BLACK = "https://tools.applemediaservices.com/api/badges/download-on-the-app-store/black/en-us?size=250x83";
const BADGE_WHITE = "https://tools.applemediaservices.com/api/badges/download-on-the-app-store/white/en-us?size=250x83";

function isDarkTheme() {
  const theme = document.body?.dataset?.theme || "";
  return theme === "steel-dark" || theme === "livesick-dark";
}

class SiteHeader extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <header class="site-header">
        <a class="brand" href="/">theolternative</a>
        <nav class="top-nav" aria-label="Primary">
          <a href="/">Home</a>
          <a href="/about/">About</a>
          <a href="/support/">Support</a>
          <a href="/privacy/">Privacy</a>
        </nav>
      </header>
    `;
  }
}

class SiteFooter extends HTMLElement {
  connectedCallback() {
    const year = new Date().getFullYear();
    this.innerHTML = `
      <footer class="site-footer">
        <nav aria-label="Footer">
          <a href="/">Home</a>
          <a href="/about/">About</a>
          <a href="/support/">Support</a>
          <a href="/privacy/">Privacy</a>
        </nav>
        <p>© ${year} theolternative</p>
      </footer>
    `;
  }
}

class AppCard extends HTMLElement {
  connectedCallback() {
    const title = this.getAttribute("title") || "";
    const slug = this.getAttribute("slug") || "";
    const summary = this.getAttribute("summary") || "";
    const label = this.getAttribute("label") || "iOS App";
    const storeId = this.getAttribute("store-id") || "";
    const internalHref = `/apps/${slug}/`;
    const appStoreHref = `https://apps.apple.com/app/${storeId}`;
    const useDarkBadge = isDarkTheme();
    const badgeUrl = useDarkBadge ? BADGE_WHITE : BADGE_BLACK;

    this.innerHTML = `
      <article class="app-card">
        <p class="app-eyebrow">${label}</p>
        <h2>${title}</h2>
        <p>${summary}</p>
        <div class="actions">
          <a class="btn" href="${internalHref}">Details</a>
          <a class="badge-link" href="${appStoreHref}" target="_blank" rel="noopener noreferrer" aria-label="Download ${title} on the App Store">
            <img src="${badgeUrl}" alt="Download on the App Store" loading="lazy">
          </a>
        </div>
      </article>
    `;
  }
}

customElements.define("site-header", SiteHeader);
customElements.define("site-footer", SiteFooter);
customElements.define("app-card", AppCard);
