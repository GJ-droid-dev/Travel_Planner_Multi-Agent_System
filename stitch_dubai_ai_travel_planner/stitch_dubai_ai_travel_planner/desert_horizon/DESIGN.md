---
name: Desert Horizon
colors:
  surface: '#faf9f5'
  surface-dim: '#dbdad6'
  surface-bright: '#faf9f5'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f4f0'
  surface-container: '#efeeea'
  surface-container-high: '#e9e8e4'
  surface-container-highest: '#e3e2df'
  on-surface: '#1b1c1a'
  on-surface-variant: '#46464d'
  inverse-surface: '#2f312e'
  inverse-on-surface: '#f2f1ed'
  outline: '#76767e'
  outline-variant: '#c6c6ce'
  surface-tint: '#575d78'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#141a32'
  on-primary-container: '#7c839f'
  inverse-primary: '#bfc5e4'
  secondary: '#006972'
  on-secondary: '#ffffff'
  secondary-container: '#9ff0fb'
  on-secondary-container: '#066f79'
  tertiary: '#735c00'
  on-tertiary: '#ffffff'
  tertiary-container: '#cba72f'
  on-tertiary-container: '#4e3d00'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dce1ff'
  primary-fixed-dim: '#bfc5e4'
  on-primary-fixed: '#141a32'
  on-primary-fixed-variant: '#3f465f'
  secondary-fixed: '#9ff0fb'
  secondary-fixed-dim: '#82d3de'
  on-secondary-fixed: '#001f23'
  on-secondary-fixed-variant: '#004f56'
  tertiary-fixed: '#ffe088'
  tertiary-fixed-dim: '#e9c349'
  on-tertiary-fixed: '#241a00'
  on-tertiary-fixed-variant: '#574500'
  background: '#faf9f5'
  on-background: '#1b1c1a'
  surface-variant: '#e3e2df'
typography:
  display-lg:
    fontFamily: Montserrat
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Montserrat
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Montserrat
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-md:
    fontFamily: Montserrat
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.05em
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-max: 1280px
  gutter: 24px
  margin-desktop: 64px
  margin-mobile: 20px
  stack-sm: 12px
  stack-md: 24px
  stack-lg: 48px
---

## Brand & Style
The design system embodies a "Modern Oasis" aesthetic—a fusion of the timeless serenity of the Arabian desert and the cutting-edge precision of Dubai’s architectural skyline. It targets affluent travelers seeking a frictionless, AI-driven planning experience that feels both authoritative and hospitable.

The visual style is **Minimalist with Tactile accents**. It leverages expansive white space (sand) to reduce cognitive load, punctuated by deep navy and teal to establish trust. The interface avoids stereotypical motifs in favor of geometric abstractions, using subtle gradients and layered surfaces to mimic the shifting light over dunes. The emotional response is one of calm confidence, efficiency, and premium service.

## Colors
The palette is rooted in the natural and architectural landscape of the region.

- **Base/Background (#FDFCF8):** A warm, off-white "Sand" used for the primary canvas to reduce eye strain and provide a premium, paper-like feel.
- **Primary Navy (#0A1128):** Used for primary text and high-contrast UI elements to ensure maximum readability and a sense of professional stability.
- **Accent Teal (#006D77):** Used for primary actions, progress indicators, and active states. It represents the Gulf waters and modern innovation.
- **Restrained Gold (#D4AF37):** Reserved for "Premium" or "AI-Suggested" features, badges, and high-value highlights. It should be used sparingly to maintain its impact.
- **Neutral Greys:** Use low-saturation navy tints for borders and secondary text to maintain harmony with the primary navy.

## Typography
The typographic hierarchy utilizes **Montserrat** for display and headings to convey a bold, modern, and geometric structural feel. **Inter** is utilized for all functional text, body copy, and UI labels due to its exceptional legibility and systematic performance.

Headings should use tight letter spacing to feel "locked in" and architectural. Body text requires generous line heights to facilitate the reading of long-form itineraries. Captions and labels often utilize slightly increased tracking and uppercase styling for a sophisticated, "wayfinding" aesthetic.

## Layout & Spacing
This design system uses a **12-column fluid grid** for desktop and a **4-column grid** for mobile. The layout philosophy is "Spacious and Structured," prioritizing breathing room between distinct itinerary days or planning modules.

- **Vertical Rhythm:** A strict 8px baseline grid ensures alignment across all components.
- **Sectioning:** Content blocks are grouped in containers with 48px to 64px of vertical padding to signify transitions between different travel stages.
- **Mobile Adaptivity:** On mobile, margins shrink to 20px, and complex data tables transform into stacked vertical cards. Horizontal swiping "carousels" are preferred for browsing landmark suggestions to preserve vertical space.

## Elevation & Depth
Depth is created through **Tonal Layers** and **Ambient Shadows** rather than harsh borders.

1.  **Level 0 (Base):** The Sand background (#FDFCF8).
2.  **Level 1 (Cards/Containers):** Pure white (#FFFFFF) surfaces with a subtle, 1px border in a very light navy-tinted grey (e.g., 5% opacity).
3.  **Shadows:** Use a "Desert Noon" shadow style—low-spread, soft, and slightly tinted with navy. 
    *   *Example:* `0px 4px 20px rgba(10, 17, 40, 0.04)`.
4.  **Interaction:** Elements should slightly lift (increase shadow spread and decrease opacity) on hover to indicate interactivity.

## Shapes
The shape language balances friendliness with architectural precision. 

- **Primary Radius:** A standard 16px (1rem) radius is applied to all primary cards, input fields, and buttons. This "Rounded" setting reflects the curvature of dunes.
- **Secondary Radius:** Smaller components like tags or chips use a 8px radius.
- **Visual Continuity:** Interactive states should never become sharp; the roundedness is a core brand pillar of "approachability."

## Components

### Buttons
- **Primary:** Deep Navy (#0A1128) background with White text. High-contrast, bold, and authoritative.
- **Secondary/Action:** Teal (#006D77) background or outline. Used for "Add to Itinerary" or "Book Now."
- **Ghost:** Transparent background with Navy text and 1px border. Used for secondary navigation like "Edit."

### Itinerary Cards
- Detailed day-by-day blocks using white backgrounds. 
- Use a left-aligned vertical timeline thread (Teal) to connect activities.
- Budget indicators are displayed as thin, horizontal bars at the bottom of the card using a gold-to-teal gradient.

### Input Fields
- Premium fields with floating labels. 
- Background: Sand (#FDFCF8) with a 1px Navy border (20% opacity).
- On focus: Border thickens and changes to Teal (#006D77) with a subtle glow.

### Workflow Timelines
- Multi-stage horizontal stepper for the planning process (e.g., Interests -> Dates -> Budget -> Generate).
- Completed steps use a Gold checkmark; active steps use a Teal ring.

### Iconography
- Line-art icons with a consistent 2px stroke weight.
- Use Teal for "utility" icons (transport, food) and Gold for "attraction" icons (landmarks, luxury experiences).

### Budget Visualization
- Horizontal bar charts within cards to show "Allocated" vs "Remaining" funds. 
- Use Teal for "within budget" and a soft Red for "over budget."