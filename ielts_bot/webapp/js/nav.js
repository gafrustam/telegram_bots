/**
 * nav.js — Mini-app switcher widget
 *
 * Usage A (auto-injects a floating 9-dot button):
 *   <script src="/assets/nav.js"></script>
 *
 * Usage B (no auto-button — wire your own trigger to window.__navOpen):
 *   <script src="/assets/nav.js" data-no-btn></script>
 *   <button onclick="window.__navOpen()">Приложения</button>
 */
(function () {
  const _me = document.currentScript;   // captured before async work
  const NO_BTN = _me && _me.hasAttribute("data-no-btn");

  const APPS = [
    {
      id: "ielts",
      emoji: "🎓",
      name: "IELTS Speaking",
      desc: "AI-оценка речи",
      url: "/ielts/",
    },
    {
      id: "ttt",
      emoji: "✕○",
      name: "Крестики-нолики",
      desc: "Ходы исчезают",
      url: "/ttt/",
    },
    {
      id: "poker",
      emoji: "♠",
      name: "Покер",
      desc: "Игра против AI",
      url: "/poker/",
    },
  ];

  function getCurrentApp() {
    const p = location.pathname;
    if (p.startsWith("/ielts")) return "ielts";
    if (p.startsWith("/ttt"))   return "ttt";
    if (p.startsWith("/poker")) return "poker";
    return null;
  }

  const CSS = `
    #_nav_btn {
      position: fixed;
      top: 14px;
      right: 14px;
      z-index: 8900;
      width: 34px;
      height: 34px;
      background: none;
      border: none;
      cursor: pointer;
      padding: 5px;
      border-radius: 8px;
      color: var(--tg-theme-hint-color, #999);
      opacity: 0.55;
      transition: opacity .2s, background .2s;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    #_nav_btn:hover, #_nav_btn:focus-visible {
      opacity: 1;
      background: rgba(128,128,128,.12);
      outline: none;
    }

    #_nav_backdrop {
      position: fixed;
      inset: 0;
      z-index: 8901;
      background: rgba(0,0,0,0);
      pointer-events: none;
      transition: background .28s;
    }
    #_nav_backdrop.open {
      background: rgba(0,0,0,.38);
      pointer-events: all;
    }

    #_nav_sheet {
      position: fixed;
      bottom: 0;
      left: 50%;
      transform: translate(-50%, 100%);
      width: 100%;
      max-width: 480px;
      z-index: 8902;
      background: var(--tg-theme-bg-color, #fff);
      border-radius: 20px 20px 0 0;
      padding: 0 18px env(safe-area-inset-bottom, 20px);
      box-shadow: 0 -6px 40px rgba(0,0,0,.13);
      transition: transform .32s cubic-bezier(.34,1.12,.64,1);
    }
    #_nav_sheet.open {
      transform: translate(-50%, 0);
    }

    ._nav_handle {
      width: 38px;
      height: 4px;
      border-radius: 2px;
      background: var(--tg-theme-hint-color, #ccc);
      opacity: .4;
      margin: 11px auto 18px;
    }

    ._nav_label {
      font-size: 11px;
      font-weight: 700;
      letter-spacing: .07em;
      text-transform: uppercase;
      color: var(--tg-theme-hint-color, #888);
      margin-bottom: 14px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    ._nav_grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      padding-bottom: 20px;
    }

    ._nav_tile {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 5px;
      padding: 14px 6px 12px;
      border-radius: 14px;
      background: var(--tg-theme-secondary-bg-color, #f0f4ff);
      text-decoration: none;
      color: var(--tg-theme-text-color, #1a1a1a);
      border: 2px solid transparent;
      cursor: pointer;
      transition: transform .12s, border-color .15s, background .15s;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      -webkit-tap-highlight-color: transparent;
    }
    ._nav_tile:hover  { text-decoration: none; }
    ._nav_tile:active { transform: scale(.93); }
    ._nav_tile.current {
      border-color: #2563eb;
      background: #fff;
      pointer-events: none;
    }

    ._nav_tile_icon { font-size: 28px; line-height: 1; }
    ._nav_tile_name {
      font-size: 12px;
      font-weight: 600;
      text-align: center;
      line-height: 1.2;
      color: var(--tg-theme-text-color, #0f172a);
    }
    ._nav_tile_desc {
      font-size: 10px;
      text-align: center;
      color: var(--tg-theme-hint-color, #64748b);
      line-height: 1.3;
    }
  `;

  const ICON_SVG = `<svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor" aria-hidden="true">
    <circle cx="3"  cy="3"  r="1.6"/>
    <circle cx="9"  cy="3"  r="1.6"/>
    <circle cx="15" cy="3"  r="1.6"/>
    <circle cx="3"  cy="9"  r="1.6"/>
    <circle cx="9"  cy="9"  r="1.6"/>
    <circle cx="15" cy="9"  r="1.6"/>
    <circle cx="3"  cy="15" r="1.6"/>
    <circle cx="9"  cy="15" r="1.6"/>
    <circle cx="15" cy="15" r="1.6"/>
  </svg>`;

  function init() {
    const style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);

    const current = getCurrentApp();

    if (!NO_BTN) {
      const btn = document.createElement("button");
      btn.id = "_nav_btn";
      btn.setAttribute("aria-label", "Приложения");
      btn.innerHTML = ICON_SVG;
      document.body.appendChild(btn);
      btn.addEventListener("click", () => (isOpen ? close() : open()));
    }

    const backdrop = document.createElement("div");
    backdrop.id = "_nav_backdrop";
    document.body.appendChild(backdrop);

    const sheet = document.createElement("div");
    sheet.id = "_nav_sheet";
    sheet.innerHTML = `
      <div class="_nav_handle"></div>
      <div class="_nav_label">Приложения</div>
      <div class="_nav_grid">
        ${APPS.map((a) => `
          <a href="${a.url}" class="_nav_tile${a.id === current ? " current" : ""}">
            <span class="_nav_tile_icon">${a.emoji}</span>
            <span class="_nav_tile_name">${a.name}</span>
            <span class="_nav_tile_desc">${a.desc}</span>
          </a>`).join("")}
      </div>`;
    document.body.appendChild(sheet);

    let isOpen = false;

    function open() {
      isOpen = true;
      backdrop.classList.add("open");
      sheet.classList.add("open");
    }
    function close() {
      isOpen = false;
      backdrop.classList.remove("open");
      sheet.classList.remove("open");
    }

    backdrop.addEventListener("click", close);

    // Swipe-down to close
    let startY = 0;
    sheet.addEventListener("touchstart", (e) => { startY = e.touches[0].clientY; }, { passive: true });
    sheet.addEventListener("touchend", (e) => {
      if (e.changedTouches[0].clientY - startY > 60) close();
    }, { passive: true });

    // Public API
    window.__navOpen  = open;
    window.__navClose = close;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
