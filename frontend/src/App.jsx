import { useState, useEffect, useMemo } from "react";
import CorePanel from "./components/CorePanel";
import SafetyPanel from "./components/SafetyPanel";
import MetricsView from "./components/MetricsView";
import DocumentationView from "./components/DocumentationView";
import benchmarkResults from "./data/benchmarkResults.json";
import metrics from "./data/metrics.json";
import { THEMES, DEFAULT_THEME_ID } from "./data/themes";
import "./App.css";

const TABS = ["Static Core Panel", "LLM + Safety Layer", "Results", "Documentation"];
const THEME_STORAGE_KEY = "safespeak-theme";

const SOCIAL_LINKS = [
  {
    href: "https://github.com/Ashma-Rai-32/safespeak-aac",
    label: "GitHub",
    icon: (
      <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
        <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.57.1.78-.25.78-.55 0-.27-.01-1-.02-1.96-3.2.7-3.88-1.54-3.88-1.54-.52-1.33-1.28-1.69-1.28-1.69-1.05-.71.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.76 2.7 1.25 3.36.96.1-.75.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.68 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.79 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.83 1.19 3.09 0 4.41-2.69 5.38-5.25 5.67.41.36.78 1.07.78 2.15 0 1.55-.01 2.8-.01 3.18 0 .31.2.66.79.55A10.5 10.5 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z" />
      </svg>
    ),
  },
  {
    href: "https://www.linkedin.com/in/ashma-rai-7880a420b/",
    label: "LinkedIn",
    icon: (
      <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
        <path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.86 0-2.15 1.45-2.15 2.95v5.66H9.34V9h3.41v1.56h.05c.48-.9 1.63-1.85 3.36-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29ZM5.34 7.43a2.07 2.07 0 1 1 0-4.13 2.07 2.07 0 0 1 0 4.13ZM7.12 20.45H3.55V9h3.57v11.45ZM22.22 0H1.77C.8 0 0 .78 0 1.75v20.5C0 23.22.8 24 1.77 24h20.45c.98 0 1.78-.78 1.78-1.75V1.75C24 .78 23.2 0 22.22 0Z" />
      </svg>
    ),
  },
];

// Blends toward black or white in sRGB space -- good enough for deriving a
// "background tint" (e.g. --danger-bg) from a theme's own accent/error color
// without needing per-theme hand-tuned values for a color Monkeytype itself
// doesn't define (they only have one semantic color, "error"; we need a
// second, "success", for our SUPPORTED vs BLOCKED distinction).
function mix(hex, targetHex, amount) {
  const h = (v) => parseInt(v, 16);
  const [r1, g1, b1] = [h(hex.slice(1, 3)), h(hex.slice(3, 5)), h(hex.slice(5, 7))];
  const [r2, g2, b2] = [h(targetHex.slice(1, 3)), h(targetHex.slice(3, 5)), h(targetHex.slice(5, 7))];
  const lerp = (a, b) => Math.round(a + (b - a) * amount);
  const toHex = (n) => n.toString(16).padStart(2, "0");
  return `#${toHex(lerp(r1, r2))}${toHex(lerp(g1, g2))}${toHex(lerp(b1, b2))}`;
}

// Is this theme's background dark or light? Used to decide which direction
// to blend a background tint (toward white on a light theme reads oddly).
function isDarkBg(hex) {
  const h = (v) => parseInt(v, 16);
  const [r, g, b] = [h(hex.slice(1, 3)), h(hex.slice(3, 5)), h(hex.slice(5, 7))];
  return (r * 299 + g * 587 + b * 114) / 1000 < 128;
}

// A fixed green, blended toward the theme's own bg, used as --success since
// Monkeytype's palette has no success/positive color to source from.
const SUCCESS_BASE = "#4ade80";
const SUCCESS_BASE_LIGHT = "#2f9e52";

function applyTheme(theme) {
  const root = document.documentElement;
  const dark = isDarkBg(theme.bg);
  const successBase = dark ? SUCCESS_BASE : SUCCESS_BASE_LIGHT;

  root.style.setProperty("--bg", theme.bg);
  root.style.setProperty("--surface", mix(theme.bg, dark ? "#ffffff" : "#000000", 0.06));
  root.style.setProperty("--sub-alt", theme.subAlt);
  root.style.setProperty("--text", theme.text);
  root.style.setProperty("--text-muted", theme.sub);
  root.style.setProperty("--border", mix(theme.bg, dark ? "#ffffff" : "#000000", 0.15));
  root.style.setProperty("--accent", theme.main);
  root.style.setProperty("--danger", theme.error);
  root.style.setProperty("--danger-bg", mix(theme.bg, theme.error, 0.18));
  root.style.setProperty("--success", successBase);
  root.style.setProperty("--success-bg", mix(theme.bg, successBase, 0.18));
}

// A favicon can't read CSS custom properties (browsers render it standalone,
// outside the page's own style context), so recoloring it on theme change
// means fetching the favicon's own SVG source, swapping its background and
// mark fills by text replacement, and pointing <link rel="icon"> at the
// resulting blob URL. Mirrors public/favicon.svg's structure: a rounded-rect
// background (theme --bg) with the logo mark (theme --accent) centered on it.
let cachedSvgTemplate = null;
let currentFaviconUrl = null;

function fetchSvgTemplate() {
  if (cachedSvgTemplate) return Promise.resolve(cachedSvgTemplate);
  return fetch("/favicon.svg")
    .then((res) => res.text())
    .then((svgText) => {
      // The background rect is the FIRST fill in the file, the two logo
      // paths share the second color. Replace by position, not by value, so
      // this doesn't depend on the specific hex codes shipped in the file.
      let fillIndex = 0;
      cachedSvgTemplate = svgText.replace(/fill="#[0-9a-fA-F]{3,8}"/g, () => {
        fillIndex += 1;
        return fillIndex === 1 ? 'fill="#BG#"' : 'fill="#MARK#"';
      });
      return cachedSvgTemplate;
    });
}

function updateFavicon(accentHex, bgHex) {
  fetchSvgTemplate()
    .then((template) => {
      const svgWithColor = template
        .replaceAll("#BG#", bgHex)
        .replaceAll("#MARK#", accentHex);
      const blob = new Blob([svgWithColor], { type: "image/svg+xml" });
      const url = URL.createObjectURL(blob);

      let link = document.querySelector("link[rel='icon']");
      if (!link) {
        link = document.createElement("link");
        link.rel = "icon";
        document.head.appendChild(link);
      }
      link.type = "image/svg+xml";
      link.href = url;

      if (currentFaviconUrl) URL.revokeObjectURL(currentFaviconUrl);
      currentFaviconUrl = url;
    })
    .catch(() => {
      // If the fetch/recolor fails for any reason (e.g. offline), leave
      // whatever favicon is already set rather than break the page.
    });
}

function App() {
  const [tab, setTab] = useState(TABS[1]);
  const [themeId, setThemeId] = useState(() => {
    try {
      return localStorage.getItem(THEME_STORAGE_KEY) || DEFAULT_THEME_ID;
    } catch {
      return DEFAULT_THEME_ID;
    }
  });

  const theme = useMemo(
    () => THEMES.find((t) => t.id === themeId) ?? THEMES[0],
    [themeId]
  );

  useEffect(() => {
    applyTheme(theme);
    updateFavicon(theme.main, theme.bg);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme.id);
    } catch {
      // localStorage unavailable (private browsing etc.), theme just won't persist
    }
  }, [theme]);

  const cycleTheme = () => {
    const currentIndex = THEMES.findIndex((t) => t.id === themeId);
    const next = THEMES[(currentIndex + 1) % THEMES.length];
    setThemeId(next.id);
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-row">
          <div className="app-title-group">
            <span className="app-logo" role="img" aria-label="SafeSpeak logo" />
            <div>
              <h1>SafeSpeak <span className="app-version">v{__APP_VERSION__}</span></h1>
              <p className="app-tagline">
                An AAC safety layer that catches AI-fabricated intent before it reaches a patient's caregiver.
              </p>
            </div>
          </div>
          <div className="header-actions">
            <div className="social-links">
              {SOCIAL_LINKS.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="social-link"
                  title={link.label}
                  aria-label={link.label}
                >
                  {link.icon}
                </a>
              ))}
            </div>
            <button className="theme-toggle" onClick={cycleTheme} title="Switch theme">
              <span className="theme-toggle-dot" />
              {theme.label}
            </button>
          </div>
        </div>
      </header>

      <nav className="tab-bar">
        {TABS.map((t) => (
          <button
            key={t}
            className={`tab-button ${tab === t ? "tab-active" : ""}`}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </nav>

      <main className="app-main">
        {tab === "Static Core Panel" && <CorePanel />}
        {tab === "LLM + Safety Layer" && <SafetyPanel benchmarkResults={benchmarkResults} />}
        {tab === "Results" && <MetricsView metrics={metrics} />}
        {tab === "Documentation" && <DocumentationView />}
      </main>
    </div>
  );
}

export default App;
