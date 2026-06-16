---
name: mph-synthwave-theme
description: Generates UI components, dashboards, and pages using Michael's signature Synthwave / TraderDaddy / Bloomberg aesthetic.
---

# mph-synthwave-theme

A core styling skill for generating web interfaces, dashboards, and UI components that perfectly match the "Momentum Phinance" (TraderDaddy) brand aesthetic. 

## When to use this skill
Use this skill when the user asks to build or style a UI, dashboard, widget, or web app, OR whenever the user mentions "my style", "my theme", "synthwave", "traderdaddy", "bloomberg terminal", or "neon".

## The Aesthetic
The visual language is a fusion of a high-performance **Bloomberg Terminal** and a sleek **Cyberpunk/Synthwave** design. It relies on extremely dark backgrounds to reduce eye strain for traders, punctuated by intense, high-contrast neon accents to draw attention to critical data.

### 1. Typography
- **Primary Data / Numbers:** `JetBrains Mono` or `Fira Code`. Use monospace fonts for all tables, ticker symbols, prices, and metrics so columns align perfectly.
- **UI / Body Text:** `Inter`, `Roboto`, or `Outfit`. Clean, legible sans-serif for general text.
- *Never use browser default fonts.*

### 2. Color Palette
- **Background:** Very dark, slightly cool grays/blacks. 
  - Main Body: `#0a0a0c`
  - Panels/Cards: `#121216` or `rgba(20, 20, 25, 0.7)` (Glassmorphism)
- **Primary Accents (Neon):**
  - **Neon Cyan:** `#00f0ff` (Used for primary borders, active states, key branding)
  - **Neon Pink:** `#ff003c` (Used for alerts, short positions, destructive actions)
  - **Neon Green:** `#00ff88` (Used for long positions, positive PnL, "EXECUTE" actions)
  - **Electric Purple:** `#b026ff` (Secondary accent)
- **Text:**
  - Primary: `#ffffff` or `#eaeaea`
  - Secondary/Muted: `#888899`

### 3. Glassmorphism & Depth
- Do not use flat, solid boxes for dashboard cards.
- Use semi-transparent backgrounds with a subtle backdrop filter.
  ```css
  background: rgba(20, 20, 25, 0.6);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  ```

### 4. Micro-animations & Glows (The "Pop")
- Interactive elements (buttons, active rows, hovered cards) must feature a distinct neon glow.
- **Buttons:** Give buttons a faint background tint of their neon color (e.g., `rgba(0, 255, 136, 0.1)`), a solid neon border, and on hover, intensify the background and add a `box-shadow` glow.
  ```css
  .btn-execute {
      background: rgba(0, 255, 136, 0.1);
      border: 1px solid #00ff88;
      color: #00ff88;
      box-shadow: 0 0 8px rgba(0, 255, 136, 0.2);
      transition: all 0.2s ease;
  }
  .btn-execute:hover {
      background: rgba(0, 255, 136, 0.2);
      box-shadow: 0 0 15px rgba(0, 255, 136, 0.5);
  }
  ```

### 5. Layout Rules
- **Density:** High density, terminal-style. Minimize whitespace where data needs to be compared, but keep it readable.
- **Grids/Borders:** Use subtle, thin lines (`1px solid rgba(255,255,255,0.1)`) to separate sections.
- **Corners:** Slight rounding (`border-radius: 4px` to `8px`), not fully pill-shaped.

## Implementation Workflow
1. If the user asks for a UI in "their style", automatically inject the CSS rules above.
2. Ensure `<link>` tags for `Inter` and `JetBrains Mono` are included via Google Fonts.
3. Review the design against the aesthetic rules: Does it look like a premium, modern, synthwave trading terminal? If not, increase the contrast and add more glassmorphism/glow.
