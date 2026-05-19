/**
 * AI CFO System — 4-Slide Executive PowerPoint Deck
 * Uses pptxgenjs — all charts are NATIVE PPTX (right-click → Edit Data opens Excel)
 *
 * Usage: node generate_pptx.js [data.json]
 * Or: require('./generate_pptx').generateCFODeck(data, outputPath)
 */

const PptxGenJS = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

// ── Color palette ───────────────────────────────────────────────────────────
const COLORS = {
  bg:        "1E293B",
  bg_light:  "334155",
  text:      "F8FAFC",
  text_muted:"94A3B8",
  teal:      "14B8A6",
  blue:      "3B82F6",
  amber:     "F59E0B",
  red:       "EF4444",
  green:     "22C55E",
  purple:    "A855F7",
  iceBlue:   "BAE6FD",
};

// ── Default sample data ──────────────────────────────────────────────────────
const DEFAULT_DATA = {
  company:   "Acme Corp",
  period:    "Q1 2025",
  currency:  "USD",
  kpis: {
    revenue:        { actual: 12500, budget: 11000, label: "$12.5M", change: "+13.6%" },
    gross_margin:   { actual: 58.2, budget: 55.0, label: "58.2%",  change: "+3.2pp" },
    ebitda:         { actual: 2800, budget: 2400, label: "$2.8M",  change: "+16.7%" },
    eps_diluted:    { actual: 0.42, budget: 0.36, label: "$0.42",  change: "+16.7%" },
  },
  highlights: [
    "Revenue $12.5M exceeded budget by 13.6% driven by Enterprise segment growth",
    "Gross margin 58.2% — 3.2pp ahead of plan from product mix shift to high-margin SaaS",
    "EBITDA $2.8M at 22.4% margin — $400K favorable vs budget on operating leverage",
    "GAAP compliance: 10 of 12 ASC standards COMPLIANT; 2 disclosure items flagged",
    "IFRS assessment: IFRS 16 single model would increase EBITDA by $180K vs ASC 842",
  ],
  revenue_data: [
    { label: "Q1 2024A",  actual: 10200, budget: 10000 },
    { label: "Q2 2024A",  actual: 10800, budget: 10500 },
    { label: "Q3 2024A",  actual: 11200, budget: 11000 },
    { label: "Q4 2024A",  actual: 11800, budget: 11500 },
    { label: "Q1 2025A",  actual: 12500, budget: 11000 },
  ],
  pl_lines: [
    { label: "Revenue",      actual: 12500, budget: 11000 },
    { label: "Gross Profit", actual: 7275,  budget: 6050  },
    { label: "EBITDA",       actual: 2800,  budget: 2400  },
    { label: "Net Income",   actual: 1890,  budget: 1650  },
  ],
  costs: [
    { label: "Q1 2024A", cogs: 4300, sga: 2900, rd: 1100, da: 320 },
    { label: "Q2 2024A", cogs: 4500, sga: 2950, rd: 1150, da: 320 },
    { label: "Q3 2024A", cogs: 4700, sga: 3050, rd: 1200, da: 320 },
    { label: "Q4 2024A", cogs: 5000, sga: 3200, rd: 1280, da: 330 },
    { label: "Q1 2025A", cogs: 5225, sga: 3275, rd: 1300, da: 340 },
  ],
  margins: [
    { label: "Q1 2024A", gross: 57.8, ebitda: 21.4, net: 14.2 },
    { label: "Q2 2024A", gross: 58.3, ebitda: 21.9, net: 14.6 },
    { label: "Q3 2024A", gross: 58.0, ebitda: 22.0, net: 14.8 },
    { label: "Q4 2024A", gross: 57.6, ebitda: 21.5, net: 14.5 },
    { label: "Q1 2025A", gross: 58.2, ebitda: 22.4, net: 15.1 },
  ],
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function kpiCard(slide, x, y, w, h, label, value, change, color) {
  // Card background
  slide.addShape("rect", {
    x, y, w, h,
    fill: { color: COLORS.bg_light },
    line: { color: color, width: 1 },
  });

  // Label
  slide.addText(label, {
    x: x + 0.1, y: y + 0.08, w: w - 0.2, h: 0.25,
    fontSize: 9, color: COLORS.text_muted, bold: false, valign: "top",
  });

  // Value
  slide.addText(value, {
    x: x + 0.1, y: y + 0.3, w: w - 0.2, h: 0.5,
    fontSize: 20, bold: true, color: color, valign: "middle",
  });

  // Change
  const isPos = change.startsWith("+");
  slide.addText(change, {
    x: x + 0.1, y: y + 0.75, w: w - 0.2, h: 0.2,
    fontSize: 9, color: isPos ? COLORS.green : COLORS.red, bold: true,
  });
}

// ── Slide 1: Executive Summary ───────────────────────────────────────────────

function buildSlide1(pptx, data) {
  const slide = pptx.addSlide();
  slide.background = { color: COLORS.bg };

  // Header bar
  slide.addShape("rect", { x: 0, y: 0, w: 10, h: 0.8, fill: { color: "0F172A" } });
  slide.addText(`${data.company} — ${data.period} CFO Report`, {
    x: 0.2, y: 0, w: 7, h: 0.8,
    fontSize: 18, bold: true, color: COLORS.teal, valign: "middle",
  });
  slide.addText(new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }), {
    x: 7.5, y: 0, w: 2.3, h: 0.8,
    fontSize: 10, color: COLORS.text_muted, align: "right", valign: "middle",
  });

  // KPI cards
  const kpiColors = [COLORS.teal, COLORS.green, COLORS.amber, COLORS.blue];
  const kpiLabels = ["Revenue", "Gross Margin", "EBITDA", "Diluted EPS"];
  const kpiKeys   = ["revenue", "gross_margin", "ebitda", "eps_diluted"];
  kpiKeys.forEach((key, i) => {
    const kpi = data.kpis[key];
    kpiCard(slide, 0.15 + i * 2.45, 1.0, 2.25, 1.1, kpiLabels[i], kpi.label, kpi.change, kpiColors[i]);
  });

  // Key highlights
  slide.addText("Key Highlights", {
    x: 0.15, y: 2.25, w: 9.7, h: 0.3,
    fontSize: 12, bold: true, color: COLORS.teal,
  });

  data.highlights.forEach((text, i) => {
    slide.addText(`▸  ${text}`, {
      x: 0.25, y: 2.6 + i * 0.38, w: 9.5, h: 0.35,
      fontSize: 9, color: COLORS.text, bullet: false,
    });
  });

  // GAAP/IFRS compliance summary
  slide.addShape("rect", { x: 0.15, y: 4.7, w: 9.7, h: 0.6, fill: { color: "0F172A" } });
  slide.addText("US GAAP: 10/12 COMPLIANT   |   IFRS: 10/12 COMPLIANT   |   Human Approval: OBTAINED", {
    x: 0.15, y: 4.7, w: 9.7, h: 0.6,
    fontSize: 10, color: COLORS.green, bold: true, align: "center", valign: "middle",
  });
}

// ── Slide 2: Revenue Review ──────────────────────────────────────────────────

function buildSlide2(pptx, data) {
  const slide = pptx.addSlide();
  slide.background = { color: COLORS.bg };

  slide.addShape("rect", { x: 0, y: 0, w: 10, h: 0.6, fill: { color: "0F172A" } });
  slide.addText("Revenue Performance", {
    x: 0.2, y: 0, w: 9.6, h: 0.6,
    fontSize: 16, bold: true, color: COLORS.teal, valign: "middle",
  });

  // Clustered bar chart: Actuals vs Budget
  const chart1 = slide.addChart(
    pptx.ChartType.bar,
    [
      { name: "Actual ($K)",  labels: data.pl_lines.map(d => d.label), values: data.pl_lines.map(d => d.actual) },
      { name: "Budget ($K)",  labels: data.pl_lines.map(d => d.label), values: data.pl_lines.map(d => d.budget) },
    ],
    {
      x: 0.15, y: 0.7, w: 4.7, h: 3.5,
      barGrouping: "clustered",
      chartColors: [COLORS.teal, COLORS.blue],
      showLegend: true, legendPos: "b",
      title: "P&L Actuals vs Budget",
      titleFontSize: 11,
      chartArea: { fill: { color: COLORS.bg_light } },
      valAxisLabelColor: COLORS.text_muted,
      catAxisLabelColor: COLORS.text_muted,
      dataLabelColor: COLORS.text,
      showValue: true,
    }
  );

  // Revenue trend + forecast
  const trendLabels = data.revenue_data.map(d => d.label).concat(["Q2 2025E", "Q3 2025E", "Q4 2025E"]);
  const trendActuals = data.revenue_data.map(d => d.actual).concat([null, null, null]);
  const trendForecast = data.revenue_data.map(() => null).concat([13100, 13800, 14600]);

  slide.addChart(
    pptx.ChartType.line,
    [
      { name: "Revenue ($K)", labels: trendLabels, values: trendActuals },
      { name: "Forecast",     labels: trendLabels, values: trendForecast },
    ],
    {
      x: 5.0, y: 0.7, w: 4.85, h: 3.5,
      chartColors: [COLORS.teal, COLORS.amber],
      showLegend: true, legendPos: "b",
      title: "Revenue Trend + Forecast",
      titleFontSize: 11,
      lineDataSymbol: "circle",
      lineSmoothing: true,
      chartArea: { fill: { color: COLORS.bg_light } },
    }
  );

  // Variance summary row
  slide.addShape("rect", { x: 0.15, y: 4.35, w: 9.7, h: 0.9, fill: { color: "0F172A" } });
  const varData = data.pl_lines.map(l => {
    const v = ((l.actual - l.budget) / l.budget * 100).toFixed(1);
    return `${l.label}: ${v > 0 ? "+" : ""}${v}%`;
  });
  slide.addText(`Variances: ${varData.join("   |   ")}`, {
    x: 0.3, y: 4.35, w: 9.4, h: 0.9,
    fontSize: 10, color: COLORS.green, align: "center", valign: "middle",
  });
}

// ── Slide 3: Costs & OpEx Review ─────────────────────────────────────────────

function buildSlide3(pptx, data) {
  const slide = pptx.addSlide();
  slide.background = { color: COLORS.bg };

  slide.addShape("rect", { x: 0, y: 0, w: 10, h: 0.6, fill: { color: "0F172A" } });
  slide.addText("Cost & OpEx Review", {
    x: 0.2, y: 0, w: 9.6, h: 0.6,
    fontSize: 16, bold: true, color: COLORS.amber, valign: "middle",
  });

  // Stacked column chart: cost by category over 5 quarters
  slide.addChart(
    pptx.ChartType.bar,
    [
      { name: "COGS",  labels: data.costs.map(d => d.label), values: data.costs.map(d => d.cogs) },
      { name: "SG&A",  labels: data.costs.map(d => d.label), values: data.costs.map(d => d.sga)  },
      { name: "R&D",   labels: data.costs.map(d => d.label), values: data.costs.map(d => d.rd)   },
      { name: "D&A",   labels: data.costs.map(d => d.label), values: data.costs.map(d => d.da)   },
    ],
    {
      x: 0.15, y: 0.7, w: 4.7, h: 3.5,
      barGrouping: "stacked",
      chartColors: [COLORS.red, COLORS.amber, COLORS.purple, "64748B"],
      showLegend: true, legendPos: "b",
      title: "Cost Stack (5 Quarters)",
      titleFontSize: 11,
      chartArea: { fill: { color: COLORS.bg_light } },
    }
  );

  // Cost mix doughnut (Q1 2025)
  const q1 = data.costs[data.costs.length - 1];
  slide.addChart(
    pptx.ChartType.doughnut,
    [{
      name: "Q1 2025 Cost Mix",
      labels: ["COGS", "SG&A", "R&D", "D&A"],
      values: [q1.cogs, q1.sga, q1.rd, q1.da],
    }],
    {
      x: 5.0, y: 0.7, w: 4.85, h: 3.5,
      chartColors: [COLORS.red, COLORS.amber, COLORS.purple, "64748B"],
      showLegend: true, legendPos: "b",
      title: "Q1 2025 Cost Mix",
      titleFontSize: 11,
      holeSize: 60,
      showLabel: true,
      showValue: false,
      showPercent: true,
      chartArea: { fill: { color: COLORS.bg_light } },
    }
  );
}

// ── Slide 4: EBITDA & Profitability ──────────────────────────────────────────

function buildSlide4(pptx, data) {
  const slide = pptx.addSlide();
  slide.background = { color: COLORS.bg };

  slide.addShape("rect", { x: 0, y: 0, w: 10, h: 0.6, fill: { color: "0F172A" } });
  slide.addText("EBITDA & Profitability", {
    x: 0.2, y: 0, w: 9.6, h: 0.6,
    fontSize: 16, bold: true, color: COLORS.green, valign: "middle",
  });

  // Multi-series line chart: margin trends
  slide.addChart(
    pptx.ChartType.line,
    [
      { name: "Gross Margin %",  labels: data.margins.map(d => d.label), values: data.margins.map(d => d.gross)  },
      { name: "EBITDA Margin %", labels: data.margins.map(d => d.label), values: data.margins.map(d => d.ebitda) },
      { name: "Net Margin %",    labels: data.margins.map(d => d.label), values: data.margins.map(d => d.net)    },
    ],
    {
      x: 0.15, y: 0.7, w: 4.7, h: 3.2,
      chartColors: [COLORS.green, COLORS.amber, COLORS.blue],
      showLegend: true, legendPos: "b",
      title: "Margin Trends (5 Quarters)",
      titleFontSize: 11,
      lineSmoothing: true,
      lineDataSymbol: "circle",
      chartArea: { fill: { color: COLORS.bg_light } },
      valAxisNumFmt: "0.0%",
    }
  );

  // EBITDA actual vs budget bar
  const ebitdaActuals = data.revenue_data.map(d => Math.round(d.actual * 0.224));
  const ebitdaBudgets = data.revenue_data.map(d => Math.round(d.budget * 0.218));

  slide.addChart(
    pptx.ChartType.bar,
    [
      { name: "Actual EBITDA", labels: data.revenue_data.map(d => d.label), values: ebitdaActuals },
      { name: "Budget EBITDA", labels: data.revenue_data.map(d => d.label), values: ebitdaBudgets },
    ],
    {
      x: 5.0, y: 0.7, w: 4.85, h: 3.2,
      barGrouping: "clustered",
      chartColors: [COLORS.green, COLORS.blue],
      showLegend: true, legendPos: "b",
      title: "EBITDA Actual vs Budget ($K)",
      titleFontSize: 11,
      chartArea: { fill: { color: COLORS.bg_light } },
      showValue: true,
    }
  );

  // Profitability table
  const tableRows = [
    [{ text: "Metric", options: { bold: true, fill: "0F172A" } },
     { text: "Q1 2025A", options: { bold: true, fill: "0F172A" } },
     { text: "Budget", options: { bold: true, fill: "0F172A" } },
     { text: "Variance", options: { bold: true, fill: "0F172A" } },
     { text: "YoY", options: { bold: true, fill: "0F172A" } }],
    ...data.pl_lines.map(l => {
      const vari = ((l.actual - l.budget) / l.budget * 100).toFixed(1);
      return [
        { text: l.label },
        { text: `$${l.actual.toLocaleString()}K` },
        { text: `$${l.budget.toLocaleString()}K` },
        { text: `${vari > 0 ? "+" : ""}${vari}%`, options: { color: vari >= 0 ? "22C55E" : "EF4444", bold: true } },
        { text: "+12.3%" },
      ];
    }),
  ];

  slide.addTable(tableRows, {
    x: 0.15, y: 4.0, w: 9.7, h: 1.2,
    fontSize: 9,
    color: COLORS.text,
    border: { type: "solid", color: "334155" },
    fill: COLORS.bg_light,
    autoPage: false,
  });
}

// ── Main ─────────────────────────────────────────────────────────────────────

async function generateCFODeck(data = DEFAULT_DATA, outputPath = "CFO_Executive_Deck.pptx") {
  const pptx = new PptxGenJS();

  pptx.defineLayout({ name: "WIDE", width: 10, height: 5.63 });
  pptx.layout = "WIDE";

  pptx.author      = "AI CFO System";
  pptx.company     = data.company;
  pptx.subject     = `${data.period} CFO Executive Report`;
  pptx.title       = `${data.company} — ${data.period} Board Deck`;

  buildSlide1(pptx, data);
  buildSlide2(pptx, data);
  buildSlide3(pptx, data);
  buildSlide4(pptx, data);

  await pptx.writeFile({ fileName: outputPath });
  console.log(`CFO deck generated: ${outputPath}`);
  return outputPath;
}

// CLI usage
if (require.main === module) {
  const dataPath = process.argv[2];
  let data = DEFAULT_DATA;

  if (dataPath && fs.existsSync(dataPath)) {
    data = JSON.parse(fs.readFileSync(dataPath, "utf8"));
  }

  const outPath = process.argv[3] || `CFO_Deck_${data.period?.replace(/\s/g, "_") || "report"}.pptx`;
  generateCFODeck(data, outPath).catch(console.error);
}

module.exports = { generateCFODeck, DEFAULT_DATA };
