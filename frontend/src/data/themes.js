// Real Monkeytype theme palettes, exact hex values extracted directly from
// Monkeytype's own compiled JS theme registry (frontend/docs/Monkeytype _ .../
// monkeytype.Oe3pEZnH.js), not approximated or guessed.
//
// Each theme's raw fields: bg, caret, main, sub, subAlt, text, error, errorExtra.
// Mapped to our CSS variables as:
//   bg -> --bg          subAlt -> --sub-alt      main/caret -> --accent
//   text -> --text       sub -> --text-muted      error -> --danger
//   errorExtra -> --danger-bg (darkened/blended, see buildThemeVars)
//
// --success/--success-bg are NOT part of Monkeytype's theme system (they
// only have one semantic "error" color) -- synthesized per theme below to
// read as "the opposite of error" within that theme's own palette.

export const THEMES = [
  { id: "9009", label: "9009", bg: "#eeebe2", caret: "#7fa480", main: "#080909", sub: "#99947f", subAlt: "#d3cfc1", text: "#080909", error: "#c87e74", errorExtra: "#a56961" },
  { id: "bingsu", label: "bingsu", bg: "#b8a7aa", caret: "#ebe6ea", main: "#83616e", sub: "#48373d", subAlt: "#ab989e", text: "#ebe6ea", error: "#921341", errorExtra: "#640b2c" },
  { id: "bliss", label: "bliss", bg: "#262727", caret: "#f0d3c9", main: "#f0d3c9", sub: "#665957", subAlt: "#343231", text: "#ffffff", error: "#bd4141", errorExtra: "#883434" },
  { id: "blue-dolphin", label: "blue dolphin", bg: "#003950", caret: "#00bcd4", main: "#ffcefb", sub: "#00e4ff", subAlt: "#014961", text: "#82eaff", error: "#ffbde6", errorExtra: "#ff8188" },
  { id: "bushido", label: "bushido", bg: "#242933", caret: "#ec4c56", main: "#ec4c56", sub: "#596172", subAlt: "#1c222d", text: "#f6f0e9", error: "#ec4c56", errorExtra: "#9b333a" },
  { id: "carbon", label: "carbon", bg: "#313131", caret: "#f66e0d", main: "#f66e0d", sub: "#616161", subAlt: "#2b2b2b", text: "#f5e6c8", error: "#e72d2d", errorExtra: "#7e2a33" },
  { id: "catppuccin", label: "catppuccin", bg: "#1e1e2e", caret: "#f2cdcd", main: "#cba6f7", sub: "#7f849c", subAlt: "#181825", text: "#cdd6f4", error: "#f38ba8", errorExtra: "#eba0ac" },
  { id: "cheesecake", label: "cheesecake", bg: "#fdf0d5", caret: "#892948", main: "#8e2949", sub: "#d91c81", subAlt: "#f3e2bf", text: "#3a3335", error: "#5cf074", errorExtra: "#5cf074" },
  { id: "copper", label: "copper", bg: "#442f29", caret: "#c25c42", main: "#b46a55", sub: "#7ebab5", subAlt: "#50362e", text: "#e7e0de", error: "#a32424", errorExtra: "#ec0909" },
  { id: "cy-red", label: "cy red", bg: "#6e2626", caret: "#541d1d", main: "#e55050", sub: "#ff6060", subAlt: "#3f1616", text: "#ffaaaa", error: "#919fd9", errorExtra: "#4d5d9e" },
  { id: "cyberspace", label: "cyberspace", bg: "#181c18", caret: "#00ce7c", main: "#00ce7c", sub: "#9578d3", subAlt: "#131613", text: "#c2fbe1", error: "#ff5f5f", errorExtra: "#d22a2a" },
  { id: "dark", label: "dark", bg: "#212b42", caret: "#962f7e", main: "#add7ff", sub: "#5c7da5", subAlt: "#1b2334", text: "#91b4d5", error: "#df4576", errorExtra: "#d996ac" },
  { id: "discord", label: "discord", bg: "#313338", caret: "#5a65ea", main: "#5a65ea", sub: "#565861", subAlt: "#2b2d31", text: "#dcdee3", error: "#df4f4b", errorExtra: "#df4f4b" },
  { id: "fire", label: "fire", bg: "#0f0000", caret: "#b31313", main: "#b31313", sub: "#683434", subAlt: "#200a0a", text: "#ffffff", error: "#2f3cb6", errorExtra: "#434a8f" },
  { id: "github", label: "github", bg: "#212830", caret: "#41ce5c", main: "#41ce5c", sub: "#788386", subAlt: "#141b23", text: "#ccdae6", error: "#c23e3a", errorExtra: "#c23e3a" },
  { id: "gruvbox-dark", label: "gruvbox dark", bg: "#282828", caret: "#fabd2f", main: "#d79921", sub: "#665c54", subAlt: "#212121", text: "#ebdbb2", error: "#fb4934", errorExtra: "#cc241d" },
  { id: "gruvbox-light", label: "gruvbox light", bg: "#fbf1c7", caret: "#689d6a", main: "#689d6a", sub: "#a89984", subAlt: "#daceae", text: "#3c3836", error: "#cc241d", errorExtra: "#9d0006" },
  { id: "hedge", label: "hedge", bg: "#415e31", caret: "#f2efbb", main: "#6a994e", sub: "#ede5b4", subAlt: "#38502a", text: "#f7f1d6", error: "#ca3d3f", errorExtra: "#782832" },
  { id: "horizon", label: "horizon", bg: "#1c1e26", caret: "#bbbbbb", main: "#c4a88a", sub: "#db886f", subAlt: "#17181f", text: "#bbbbbb", error: "#d55170", errorExtra: "#ff3d3d" },
  { id: "lilac-mist", label: "lilac mist", bg: "#fffbfe", caret: "#e099d6", main: "#b94189", sub: "#e094c2", subAlt: "#ecdcee", text: "#5c2954", error: "#ff6f69", errorExtra: "#ff6f69" },
  { id: "mashu", label: "mashu", bg: "#2b2b2c", caret: "#76689a", main: "#76689a", sub: "#d8a0a6", subAlt: "#27242c", text: "#f1e2e4", error: "#d44729", errorExtra: "#8f2f19" },
  { id: "matcha-moccha", label: "matcha moccha", bg: "#523525", caret: "#7ec160", main: "#7ec160", sub: "#9e6749", subAlt: "#422b1e", text: "#ecddcc", error: "#fb4934", errorExtra: "#cc241d" },
  { id: "matrix", label: "matrix", bg: "#000000", caret: "#15ff00", main: "#15ff00", sub: "#006500", subAlt: "#032000", text: "#d1ffcd", error: "#da3333", errorExtra: "#791717" },
  { id: "monokai", label: "monokai", bg: "#272822", caret: "#66d9ef", main: "#a6e22e", sub: "#e6db74", subAlt: "#1f201b", text: "#e2e2dc", error: "#f92672", errorExtra: "#fd971f" },
  { id: "pale-nimbus", label: "pale nimbus", bg: "#433e4c", caret: "#9efffd", main: "#94ffc2", sub: "#ffaca3", subAlt: "#694f5e", text: "#feffdb", error: "#ff5c5c", errorExtra: "#ff0000" },
  { id: "paper", label: "paper", bg: "#eeeeee", caret: "#444444", main: "#444444", sub: "#b2b2b2", subAlt: "#dddddd", text: "#444444", error: "#d70000", errorExtra: "#d70000" },
  { id: "red-dragon", label: "red dragon", bg: "#1a0b0c", caret: "#ff3a32", main: "#ff3a32", sub: "#e2a528", subAlt: "#0e0506", text: "#4a4d4e", error: "#771b1f", errorExtra: "#591317" },
  { id: "serika-dark", label: "serika dark", bg: "#323437", caret: "#e2b714", main: "#e2b714", sub: "#646669", subAlt: "#2c2e31", text: "#d1d0c5", error: "#ca4754", errorExtra: "#7e2a33" },
  { id: "solarized-dark", label: "solarized dark", bg: "#002b36", caret: "#dc322f", main: "#859900", sub: "#2aa198", subAlt: "#00222b", text: "#268bd2", error: "#d33682", errorExtra: "#9b225c" },
  { id: "solarized-light", label: "solarized light", bg: "#fdf6e3", caret: "#dc322f", main: "#859900", sub: "#2aa198", subAlt: "#e2d8be", text: "#181819", error: "#d33682", errorExtra: "#9b225c" },
  { id: "solarized-osaka", label: "solarized osaka", bg: "#00141a", caret: "#b58900", main: "#859900", sub: "#2aa198", subAlt: "#00222b", text: "#eee8d5", error: "#dc322f", errorExtra: "#9b225c" },
];

export const DEFAULT_THEME_ID = "serika-dark";
