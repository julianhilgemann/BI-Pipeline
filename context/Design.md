This is the **Corporate Design & Data Visualization Guide** for Vantage Alpin.

**Role:** Creative Director / UI Lead
**Audience:** UI/UX Designer & Power BI Developer
**Objective:** Translate the "Vantage Alpin" brand identity into a functional, premium Data Design System. The dashboard must look like it belongs in the same ecosystem as their €800 Gore-Tex jackets—technical, precise, and uncompromising.

---

# Design Specification: Vantage Alpin Analytics

## 1. Brand Philosophy: "Alpine Precision"
Vantage Alpin is not a lifestyle brand; it is an equipment brand. Our users (CFO, Logistics, Marketing) are navigating high-risk terrain (profitability margins).
*   **Keywords:** Technical, Austere, Legible, High-Contrast, Swiss-Style.
*   **The Metaphor:** The **"Altimeter."** The dashboard is not a marketing brochure; it is a precision instrument. If the needle is wrong, you crash.
*   **Anti-Patterns:** No drop shadows, no gradients, no "cute" rounded corners, no decorative illustrations.

---

## 2. Typography System (The "Swiss Style")
We use a typographic hierarchy rooted in the **International Typographic Style** (Swiss Design). It relies on grids, asymmetry, and sans-serif typefaces.

*   **Primary Font (Headlines/KPIs):** **DIN Pro** (or *DIN 1451*).
    *   *Why:* It is the standard for German industrial engineering and road signage. It screams "Technical German Brand."
    *   *Usage:* KPI Numbers, Section Headers.
    *   *Weight:* Bold / Medium.
*   **Secondary Font (Body/Labels):** **Inter** (or *Roboto*).
    *   *Why:* Highly legible on screens at small sizes (axis labels, tooltips).
    *   *Usage:* Axis text, filters, body copy.
*   **Hierarchy:**
    *   **KPI Big:** 42pt DIN Bold (Dark Slate).
    *   **Section Header:** 18pt DIN Medium (Uppér-case, tracked out +10%).
    *   **Label:** 10pt Inter Regular (Grey 600).

---

## 3. Color Palette: "Rock, Ice, & Signal"
We avoid the standard "Traffic Light" (Red/Green/Yellow) colors, which look cheap. We use a palette derived from the alpine environment.

### 3.1 The UI Foundation (The Mountain)
*   **Glacial White (Background):** `#F8F9FA` (Not pure white, reduces eye strain).
*   **Granite (Text/Primary):** `#212529` (Almost black, high contrast).
*   **Limestone (Borders/Dividers):** `#DEE2E6` (Subtle structure).

### 3.2 The Data Encodings (The Information)
These colors have semantic meaning. **Do not deviate.**

*   **Metric: Revenue / Volume (Neutral Good)**
    *   *Color:* **Deep Slate Blue**
    *   *Hex:* `#343A40` or `#495057`
    *   *Concept:* The mountain rock. Solid, foundational.

*   **Metric: Profit / Margin (Positive)**
    *   *Color:* **Alpine Spruce**
    *   *Hex:* `#2B8A3E` (A deep, cold green. Not "Lime" green).
    *   *Concept:* Growth, stability.

*   **Metric: Returns / Loss / Costs (Negative)**
    *   *Color:* **Rescue Orange** (Vantage Alpin Brand Color)
    *   *Hex:* `#F03E3E` or `#FD7E14` (High visibility).
    *   *Concept:* Danger, attention required. "Signal flare."

*   **Metric: Forecast / Budget (Hypothetical)**
    *   *Color:* **Mist Grey**
    *   *Hex:* `#ADB5BD` (Dashed lines).
    *   *Concept:* Not yet real.

---

## 4. Component Library & Shapes

### 4.1 Card Design (The "Module")
*   **Shape:** **Sharp corners (0px radius).** Rounded corners imply softness/consumer tech. Vantage is hardware.
*   **Border:** 1px Solid `#DEE2E6` on the Left only (The "Accent Stripe").
*   **Background:** White `#FFFFFF`.
*   **Behavior:** Minimal padding. Content is king.

### 4.2 Chart Styling Guidelines
*   **Gridlines:** Horizontal only. Light Grey (`#F1F3F5`). Dotted.
*   **Axis Lines:** Remove Y-Axis lines. Keep X-Axis baseline.
*   **Data Labels:** On *inside end* of bars if possible, or directly above. Remove Y-Axis text if labels are present (Data-Ink Ratio).
*   **Interactive States:** Hovering dims non-selected elements by 50%.

---

## 5. Visualization "Recipes" for Key Problems

Here is how you visualize the specific client pain points using this design system.

### 5.1 The "Swiss Surcharge" (Geography)
*   **Visual:** Chloropleth Map (Custom Shape Map for DACH).
*   **The Twist:** Do not color by Revenue. Color by **Contribution Margin %**.
*   **Palette:** Diverging.
    *   *Midpoint (0% Margin):* Light Grey.
    *   *Positive:* Deep Spruce.
    *   *Negative:* Rescue Orange.
*   **Effect:** Germany might look dark green (healthy), while Switzerland lights up in Orange despite high sales volume. This visually proves the "Surcharge" problem instantly.

### 5.2 The "Cinderella Effect" (Returns Analysis)
*   **Visual:** "Erosion" Bar Chart (Stacked Column).
*   **Composition:**
    *   **Bottom Stack (Solid Slate):** Net Revenue (The money we keep).
    *   **Top Stack (Hashed Pattern / Rescue Orange):** Returns (The money we lost).
*   **Design Note:** Use a pattern (diagonal lines) for the Return segment. This makes it look like "damaged" or "removed" material.
*   **Story:** The user sees a massive "Erosion" block on the *Footwear* bar compared to a tiny one on *Ropes*.

### 5.3 Marketing Attribution (The Waterfall)
*   **Visual:** "Step-Down" Waterfall.
*   **Flow:**
    1.  Start: **Gross Sales** (Slate Grey).
    2.  Step Down: **Returns** (Rescue Orange).
    3.  Step Down: **COGS** (Light Grey).
    4.  Step Down: **Logistics** (Light Grey).
    5.  Step Down: **Marketing** (Purple/Accent - to isolate this specific cost).
    6.  End: **Net Profit** (Spruce Green).
*   **Emphasis:** Highlight the "Marketing" step. Maybe add a connector line showing which product groups have the steepest marketing drop.

---

## 6. Implementation Guide (Power BI JSON Theme)

To ensure the developer follows this, create a `vantage_theme.json`.

```json
{
  "name": "Vantage Alpin Technical",
  "dataColors": ["#343A40", "#2B8A3E", "#F03E3E", "#ADB5BD"],
  "visualStyles": {
    "*": {
      "*": {
        "title": [{ "fontFace": "DIN Pro", "fontSize": 12, "color": "#212529" }],
        "background": [{ "transparency": 0 }],
        "border": [{ "show": false }],
        "outspace": [{ "color": "#F8F9FA" }]
      }
    },
    "card": {
      "*": {
        "labels": [{ "fontFace": "DIN Pro", "fontSize": 30, "color": "#212529" }],
        "categoryLabels": [{ "fontFace": "Inter", "fontSize": 10, "color": "#868E96" }]
      }
    }
  }
}
```

---

## 7. Deliverables Checklist

As the Designer, you are responsible for handing over:
1.  **Figma Mockups:** High-fidelity pixel-perfect screens of the 3 main views.
2.  **Icon Set (SVG):** Custom icons for *Logistics* (Box), *Margin* (Delta), *Product* (Carabiner/Boot).
3.  **JSON Theme File:** For Power BI automation.
4.  **Style Guide PDF:** One-pager cheating sheet for the developers (Hex codes + Fonts).

**Final Note:**
"If it looks like a spreadsheet, it's boring. If it looks like a video game, it's unprofessional. It must look like a **Swiss Bank Statement meets a Mountaineering GPS.**"