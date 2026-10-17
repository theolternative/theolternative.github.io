/* Teams page (/apps/steel-profiles-pro/teams/): reveals, the pinned hero reel,
   the cost figure with the request email, and the question field. Everything
   on the page is readable without this script. */

(() => {
  const STORE_PRO = "https://apps.apple.com/app/id662511256";
  const PAGE = "https://theolternative.com/apps/steel-profiles-pro/teams/";
  // App Store prices (Steel Profiles Pro; All Libraries in the free app), checked 2026-10-17
  const PRICES = {
    USD: { pro: 9.99, all: 6.99 },
    EUR: { pro: 9.99, all: 7.99 },
    GBP: { pro: 9.99, all: 6.99 },
    CAD: { pro: 12.99, all: 9.99 },
    AUD: { pro: 14.99, all: 9.99 },
    NZD: { pro: 19.99, all: 12.99 },
    CHF: { pro: 9, all: 6 },
    JPY: { pro: 1500, all: 1100 },
  };

  /* ---------- reveal once ---------- */
  const targets = document.querySelectorAll(".tp [data-reveal]");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue;
        e.target.classList.add("is-in");
        io.unobserve(e.target);
      }
    }, { rootMargin: "0px 0px -10% 0px", threshold: 0.08 });
    targets.forEach((el) => io.observe(el));
    window.addEventListener("load", () => setTimeout(() => {
      targets.forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.top < innerHeight && r.bottom > 0) el.classList.add("is-in");
      });
    }, 2500));
  } else {
    targets.forEach((el) => el.classList.add("is-in"));
  }

  /* ---------- hero: the sentence holds while the reel advances ---------- */
  const hero = document.querySelector(".tp-hero");
  if (hero) {
    const stage = hero.querySelector(".tp-stage");
    const frames = [...hero.querySelectorAll(".tp-frame")];
    const reel = hero.querySelector(".tp-reel");
    const caption = hero.querySelector(".tp-caption");
    const headerH = () => document.querySelector("header.site-header")?.offsetHeight || 52;
    let current = -1;

    // frames[0] is the list the visitor came from; the steps centre frames 1 to 4
    const show = (k) => {
      if (k === current) return;
      current = k;
      reel.style.setProperty("--k", k);
      frames.forEach((f, i) => f.classList.toggle("is-current", i === k));
      caption.textContent = frames[k].dataset.caption || "";
    };

    const layout = () => {
      hero.classList.add("is-pinned");
      stage.style.height = "auto";
      const available = innerHeight - headerH();
      const wide = matchMedia("(min-width: 1024px)").matches;
      let needed;
      if (wide) {
        const frame = frames[1].offsetHeight;
        const foot = hero.querySelector(".tp-hero-foot").offsetHeight;
        needed = frame + 2 * (foot + 64);
      } else {
        needed = stage.scrollHeight;
      }
      stage.style.height = "";
      if (needed > available) {
        hero.classList.remove("is-pinned");
        frames.forEach((f) => f.classList.remove("is-current"));
        current = -1;
        return;
      }
      hero.style.setProperty("--step", "45vh");
      onScroll();
    };

    const onScroll = () => {
      if (!hero.classList.contains("is-pinned")) return;
      const travel = hero.offsetHeight - stage.offsetHeight;
      const p = Math.min(1, Math.max(0, -hero.getBoundingClientRect().top / Math.max(1, travel)));
      const step = p < 0.2 ? 0 : p < 0.5 ? 1 : p < 0.8 ? 2 : 3;
      show(Math.min(step + 1, frames.length - 1));
    };

    let ticking = false;
    window.addEventListener("scroll", () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => { ticking = false; onScroll(); });
    }, { passive: true });
    let resizeTimer;
    window.addEventListener("resize", () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(layout, 150); });
    layout();
    window.addEventListener("load", layout);
  }

  /* ---------- cost: plan names, one live figure, the request email ---------- */
  const cost = document.querySelector(".tp-cost");
  if (cost) {
    const plans = [...cost.querySelectorAll(".tp-plan")];
    const stages = Object.fromEntries([...cost.querySelectorAll(".tp-price-plan")].map((el) => [el.dataset.for, el]));
    const currencySelects = [...cost.querySelectorAll('[data-in="currency"]')];

    const guessCurrency = () => {
      const langs = navigator.languages?.length ? navigator.languages : [navigator.language || "en-US"];
      for (const tag of langs) {
        const parts = tag.split("-");
        const region = (parts.find((p, i) => i > 0 && p.length === 2) || "").toUpperCase();
        const lang = parts[0].toLowerCase();
        if (region === "GB") return "GBP";
        if (region === "CA") return "CAD";
        if (region === "AU") return "AUD";
        if (region === "NZ") return "NZD";
        if (region === "CH") return "CHF";
        if (region === "JP" || lang === "ja") return "JPY";
        if (["AT", "BE", "CY", "DE", "EE", "ES", "FI", "FR", "GR", "HR", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PT", "SI", "SK"].includes(region)) return "EUR";
        if (!region && ["de", "fr", "it", "es", "nl", "pt", "fi", "el", "sk", "sl", "et", "lv", "lt"].includes(lang)) return "EUR";
        if (region) return "USD";
      }
      return "USD";
    };
    let currency = guessCurrency();

    const money = (value, cur) => new Intl.NumberFormat("en-GB", {
      style: "currency", currency: cur,
      minimumFractionDigits: cur === "JPY" ? 0 : 2, maximumFractionDigits: cur === "JPY" ? 0 : 2,
    }).format(value);
    const round = (v, cur) => cur === "JPY" ? Math.round(v) : Math.round(v * 100) / 100;

    const copiesOf = (plan) => {
      const input = stages[plan]?.querySelector('[data-in="copies"]');
      if (!input) return 1;
      const n = Math.round(Number(input.value));
      return Number.isFinite(n) ? Math.min(5000, Math.max(1, n)) : 1;
    };

    const requestText = (plan, n, unit, total, discounted) => {
      const school = plan === "school";
      const portal = school ? "Apple School Manager (school.apple.com)" : "Apple Business (business.apple.com)";
      const path = school ? "Apps and Books" : "Apps & Services > Apps and Books";
      const lines = [
        "Hello,",
        "",
        `could we buy ${n} ${n === 1 ? "copy" : "copies"} of Steel Profiles Pro for our ${school ? "school's" : "team's"} iPhones and iPads?`,
        "",
        `App: Steel Profiles Pro by theolternative, for iPhone and iPad`,
        `App Store: ${STORE_PRO}`,
        `Price: ${unit} a copy${discounted ? " less the 50% education discount for 20 copies or more" : ""}, about ${total} in total. Apple shows the final amount with any tax before payment.`,
        "",
        `How: in ${portal}, open ${path}, search for "Steel Profiles Pro", enter ${n} licences and buy. Then assign them to our devices or users in device management.`,
        "",
        "Every library and the design checks are included, so there is nothing to unlock on the devices.",
        `Details: ${PAGE}`,
        "",
        "Thank you",
      ];
      return lines.join("\n");
    };

    const render = () => {
      const p = PRICES[currency];
      currencySelects.forEach((s) => { s.value = currency; });

      const one = stages.one;
      one.querySelector('[data-out="figure"]').textContent = money(p.all, currency);

      for (const plan of ["company", "school"]) {
        const el = stages[plan];
        const n = copiesOf(plan);
        const discounted = plan === "school" && n >= 20;
        const total = round(p.pro * n * (discounted ? 0.5 : 1), currency);
        el.querySelector('[data-out="figure"]').textContent = money(total, currency);
        const unit = money(p.pro, currency);
        el.querySelector('[data-out="period"]').textContent = plan === "school"
          ? (discounted ? `for ${n} copies at half of ${unit} each` : `for ${n} ${n === 1 ? "copy" : "copies"} at ${unit} each: half price starts at 20`)
          : `for ${n} ${n === 1 ? "copy" : "copies"} at ${unit} each, paid once`;
        const body = requestText(plan, n, unit, money(total, currency), discounted);
        const subject = `Steel Profiles Pro: ${n} ${n === 1 ? "copy" : "copies"} for our ${plan === "school" ? "school" : "team"}`;
        const link = el.querySelector('[data-out="request"]');
        link.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
        link.dataset.body = body;
      }
    };

    const select = (plan, focus) => {
      plans.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.plan === plan)));
      Object.entries(stages).forEach(([key, el]) => el.classList.toggle("is-on", key === plan));
      if (focus) plans.find((b) => b.dataset.plan === plan)?.focus();
    };

    plans.forEach((b, i) => {
      b.addEventListener("click", () => select(b.dataset.plan));
      b.addEventListener("keydown", (e) => {
        const d = e.key === "ArrowDown" || e.key === "ArrowRight" ? 1 : e.key === "ArrowUp" || e.key === "ArrowLeft" ? -1 : 0;
        if (!d) return;
        e.preventDefault();
        select(plans[(i + d + plans.length) % plans.length].dataset.plan, true);
      });
    });

    // On phones the selected plan's figure sits directly under its name
    const phone = matchMedia("(max-width: 1023px)");
    const place = () => {
      Object.entries(stages).forEach(([key, el]) => {
        const button = plans.find((b) => b.dataset.plan === key);
        if (phone.matches) button.after(el);
        else cost.querySelector(".tp-price").append(el);
      });
    };
    phone.addEventListener?.("change", place);
    place();

    cost.querySelectorAll(".tp-calc").forEach((c) => { c.hidden = false; });
    cost.querySelectorAll('[data-in="copies"]').forEach((input) => {
      input.addEventListener("input", render);
      input.addEventListener("change", () => { input.value = copiesOf(input.closest(".tp-price-plan").dataset.for); render(); });
    });
    cost.querySelectorAll("[data-step]").forEach((b) => {
      b.addEventListener("click", () => {
        const input = b.parentElement.querySelector("input");
        input.value = Math.min(5000, Math.max(1, (Number(input.value) || 0) + Number(b.dataset.step)));
        render();
      });
    });
    currencySelects.forEach((s) => s.addEventListener("change", () => { currency = s.value; render(); }));

    if (navigator.clipboard) {
      cost.querySelectorAll(".tp-copy").forEach((b) => {
        b.hidden = false;
        b.addEventListener("click", async () => {
          const link = b.closest(".tp-price-plan").querySelector('[data-out="request"]');
          try {
            await navigator.clipboard.writeText(link.dataset.body || "");
            b.textContent = "Copied";
          } catch {
            b.textContent = "Copy failed";
          }
          setTimeout(() => { b.textContent = "Copy the request"; }, 2000);
        });
      });
    }

    select("company");
    render();
  }

  /* ---------- the film plays only while it is on screen ---------- */
  const film = document.querySelector(".tp-film");
  if (film && "IntersectionObserver" in window) {
    const still = matchMedia("(prefers-reduced-motion: reduce)");
    const io = new IntersectionObserver(([e]) => {
      if (e.isIntersecting && !still.matches) {
        film.preload = "auto";
        film.play().catch(() => {});
      } else {
        film.pause();
      }
    }, { threshold: 0.25 });
    io.observe(film);
  }

  /* ---------- one question, by email ---------- */
  const form = document.querySelector(".tp-ask-form");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const q = form.querySelector("#tp-question").value.trim();
      const subject = "Steel Profiles Pro for teams";
      window.location.href = `mailto:support@theolternative.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(q)}`;
    });
  }

})();
