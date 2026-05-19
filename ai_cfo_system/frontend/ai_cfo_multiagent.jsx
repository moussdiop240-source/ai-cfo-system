/**
 * AI CFO Multi-Agent UI
 * Main interface: Task submission, pipeline status, GAAP/IFRS results, HITL approval, Debate
 */
import React, { useState, useEffect, useRef } from "react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

const COLORS = {
  bg:       "#04060F",
  card:     "#0B1120",
  cyan:     "#00FFC8",
  blue:     "#60A5FA",
  amber:    "#FBBF24",
  red:      "#F87171",
  green:    "#10B981",
  purple:   "#A78BFA",
  muted:    "#4E6880",
};

const styles = {
  app:       { background: COLORS.bg, minHeight: "100vh", color: "#F1F5F9", fontFamily: "'Segoe UI', system-ui, sans-serif", padding: "24px" },
  card:      { background: COLORS.card, borderRadius: 12, border: "1px solid rgba(255,255,255,0.08)", padding: 24, marginBottom: 20 },
  glowCard:  { background: "rgba(11,17,32,0.8)", backdropFilter: "blur(20px)", borderRadius: 12, border: `1px solid rgba(0,255,200,0.2)`, padding: 24, marginBottom: 20, boxShadow: "0 0 20px rgba(0,255,200,0.08)" },
  input:     { background: "#0F172A", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#F1F5F9", padding: "10px 14px", fontSize: 14, width: "100%", outline: "none" },
  textarea:  { background: "#0F172A", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#F1F5F9", padding: "10px 14px", fontSize: 13, width: "100%", fontFamily: "'Courier New', monospace", resize: "vertical", outline: "none", minHeight: 160 },
  btnPrimary:{ background: `linear-gradient(135deg, ${COLORS.cyan}, ${COLORS.blue})`, color: "#0B1120", border: "none", borderRadius: 8, padding: "12px 28px", fontSize: 14, fontWeight: 700, cursor: "pointer" },
  btnSecondary:{ background: "transparent", border: `1px solid ${COLORS.blue}`, color: COLORS.blue, borderRadius: 8, padding: "10px 20px", fontSize: 13, cursor: "pointer" },
  btnDanger: { background: "transparent", border: `1px solid ${COLORS.red}`, color: COLORS.red, borderRadius: 8, padding: "10px 20px", fontSize: 13, cursor: "pointer" },
  label:     { fontSize: 12, color: COLORS.muted, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6, display: "block" },
  tag:       (color) => ({ background: `rgba(${hexToRgb(color)},0.15)`, color, border: `1px solid rgba(${hexToRgb(color)},0.3)`, borderRadius: 12, padding: "3px 10px", fontSize: 11, fontWeight: 600 }),
  grid2:     { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 },
  grid3:     { display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 },
};

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `${r},${g},${b}`;
}

// ── KPI Card ─────────────────────────────────────────────────────────────────
function KpiCard({ label, value, unit = "", color = COLORS.cyan }) {
  return (
    <div style={{ background: COLORS.card, borderRadius: 12, padding: 20, border: `1px solid rgba(${hexToRgb(color)},0.2)`, boxShadow: `0 0 20px rgba(${hexToRgb(color)},0.06)` }}>
      <div style={{ fontSize: 11, color: COLORS.muted, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 700, fontFamily: "'Courier New', monospace", color, textShadow: `0 0 15px rgba(${hexToRgb(color)},0.5)` }}>
        {value !== null && value !== undefined ? value : "—"}{unit}
      </div>
    </div>
  );
}

// ── Compliance Status Badge ───────────────────────────────────────────────────
function ComplianceBadge({ status }) {
  const cfg = {
    COMPLIANT:           { color: COLORS.green, label: "✓ COMPLIANT" },
    DISCLOSURE_REQUIRED: { color: COLORS.amber, label: "⚠ DISCLOSURE" },
    NON_COMPLIANT:       { color: COLORS.red,   label: "✗ NON-COMPLIANT" },
  }[status] || { color: COLORS.muted, label: "— UNKNOWN" };
  return <span style={styles.tag(cfg.color)}>{cfg.label}</span>;
}

// ── Agent Status Pipeline ─────────────────────────────────────────────────────
function PipelineStatus({ statuses }) {
  const agents = ["data_agent","math_engine","rag_agent","gaap_agent","ifrs_agent","analysis_agent","human_review","reporting_agent"];
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      {agents.map(a => {
        const s = statuses?.[a];
        const color = s === "complete" ? COLORS.green : s === "error" ? COLORS.red : s === "pending" ? COLORS.amber : COLORS.muted;
        return (
          <div key={a} style={{ display: "flex", alignItems: "center", gap: 6, background: `rgba(${hexToRgb(color)},0.1)`, border: `1px solid rgba(${hexToRgb(color)},0.3)`, borderRadius: 8, padding: "4px 10px" }}>
            <div style={{ width: 6, height: 6, borderRadius: "50%", background: color }} />
            <span style={{ fontSize: 11, color }}>{a.replace("_", " ")}</span>
          </div>
        );
      })}
    </div>
  );
}

// ── Compliance Table ──────────────────────────────────────────────────────────
function ComplianceTable({ results, title }) {
  if (!results || !Object.keys(results).length) return null;
  return (
    <div style={{ ...styles.card, marginBottom: 0 }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: "#94A3B8", marginBottom: 16, textTransform: "uppercase", letterSpacing: "0.05em" }}>{title}</div>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
        <thead>
          <tr style={{ background: "#050810" }}>
            {["Standard","Status","Finding","Key Difference"].map(h => (
              <th key={h} style={{ padding: "8px 12px", textAlign: "left", color: COLORS.muted, fontWeight: 600, borderBottom: "1px solid rgba(255,255,255,0.06)" }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.entries(results).map(([key, r]) => (
            <tr key={key} style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
              <td style={{ padding: "8px 12px", color: COLORS.blue, fontWeight: 600 }}>{r.standard || key.toUpperCase()}</td>
              <td style={{ padding: "8px 12px" }}><ComplianceBadge status={r.status} /></td>
              <td style={{ padding: "8px 12px", color: "#94A3B8", maxWidth: 360 }}>{(r.finding || "").slice(0, 120)}{r.finding?.length > 120 ? "…" : ""}</td>
              <td style={{ padding: "8px 12px", color: COLORS.muted, maxWidth: 200, fontSize: 11 }}>{(r.key_difference_from_ifrs || r.key_difference_from_gaap || r.key_rule || "").slice(0, 100)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function AICFOMultiAgent() {
  const [tab, setTab] = useState("task");
  const [taskForm, setTaskForm] = useState({
    company_name: "Acme Corp",
    period: "Q1 2025",
    task_type: "full_report",
    report_format: "board",
    task_description: "Quarterly board report with GAAP/IFRS compliance analysis",
    submitted_by: "cfo@company.com",
    raw_financial_data: JSON.stringify({
      revenue: 12500000, cogs: 5225000, gross_profit: 7275000,
      ebitda: 2800000, net_income: 1890000,
      total_assets: 45000000, total_equity: 28000000,
      current_assets: 18000000, current_liabilities: 8500000,
      cash: 6200000, total_debt: 12000000,
      accounts_receivable: 4200000, inventory: 1800000,
      goodwill: 5000000, rou_assets: 2400000, lease_liability: 2200000,
      rd_expense: 1300000, sga_expense: 3275000,
      shares_outstanding: 4500000, diluted_shares: 4750000,
      actuals: { revenue: 12500000, cogs: 5225000, ebitda: 2800000 },
      budget:  { revenue: 11000000, cogs: 5000000, ebitda: 2400000 },
      historical_revenue: [9800000, 10200000, 10800000, 11200000, 11800000, 12500000],
    }, null, 2),
  });

  const [taskId, setTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [debateForm, setDebateForm] = useState({
    company_name: "Acme Corp",
    period: "Q1 2025",
    jurisdiction: "United States",
    listing_exchange: "NASDAQ",
    industry: "Technology",
    financial_data: taskForm.raw_financial_data,
  });
  const [debateResult, setDebateResult] = useState(null);
  const [debateLoading, setDebateLoading] = useState(false);

  const [approvalForm, setApprovalForm] = useState({ decision: "approved", feedback: "", approved_by: "CFO" });

  const pollRef = useRef(null);

  // Poll task status
  useEffect(() => {
    if (!taskId) return;
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/tasks/${taskId}`);
        const data = await res.json();
        setTaskStatus(data);
        if (["complete", "error"].includes(data.status)) {
          clearInterval(pollRef.current);
          if (data.status === "complete") {
            // Fetch full report
            const rres = await fetch(`${API_BASE}/tasks/${taskId}/report`);
            if (rres.ok) {
              const rdata = await rres.json();
              setTaskStatus(prev => ({ ...prev, ...rdata }));
            }
          }
        }
      } catch (e) { /* silent */ }
    }, 2500);
    return () => clearInterval(pollRef.current);
  }, [taskId]);

  async function submitTask() {
    setLoading(true); setError(null);
    try {
      let financialData;
      try { financialData = JSON.parse(taskForm.raw_financial_data); }
      catch { throw new Error("Invalid JSON in financial data"); }

      const res = await fetch(`${API_BASE}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...taskForm, raw_financial_data: financialData }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Submit failed");
      setTaskId(data.task_id);
      setTab("status");
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }

  async function submitApproval() {
    if (!taskId) return;
    try {
      const res = await fetch(`${API_BASE}/approvals/${taskId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(approvalForm),
      });
      const data = await res.json();
      alert(`Approval submitted: ${data.message}`);
    } catch (e) { alert(`Error: ${e.message}`); }
  }

  async function runDebate() {
    setDebateLoading(true);
    try {
      let financialData;
      try { financialData = JSON.parse(debateForm.financial_data); }
      catch { throw new Error("Invalid JSON in financial data"); }

      const res = await fetch(`${API_BASE}/debate/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...debateForm, financial_data: financialData }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Debate failed");
      setDebateResult(data);
    } catch (e) { alert(`Debate error: ${e.message}`); }
    finally { setDebateLoading(false); }
  }

  const tabStyle = (t) => ({
    padding: "10px 20px", cursor: "pointer", fontSize: 13, fontWeight: 600,
    color: tab === t ? COLORS.cyan : COLORS.muted,
    borderBottom: tab === t ? `2px solid ${COLORS.cyan}` : "2px solid transparent",
    background: "transparent", border: "none",
  });

  return (
    <div style={styles.app}>
      {/* Header */}
      <div style={{ ...styles.glowCard, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, background: `linear-gradient(135deg, ${COLORS.cyan}, ${COLORS.blue})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            AI CFO System
          </div>
          <div style={{ fontSize: 12, color: COLORS.muted, marginTop: 2 }}>
            Multi-Agent Financial Intelligence · 12 GAAP + 12 IFRS Standards · LangGraph + RAG + HITL
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {["task","status","debate"].map(t => (
            <button key={t} style={tabStyle(t)} onClick={() => setTab(t)}>
              {t === "task" ? "Submit Task" : t === "status" ? "Pipeline Status" : "GAAP/IFRS Debate"}
            </button>
          ))}
        </div>
      </div>

      {/* ── Task Submission ── */}
      {tab === "task" && (
        <div>
          <div style={styles.card}>
            <div style={{ fontSize: 14, fontWeight: 600, color: "#94A3B8", marginBottom: 20, textTransform: "uppercase", letterSpacing: "0.05em" }}>Submit Financial Analysis Task</div>
            <div style={styles.grid2}>
              {[["Company Name", "company_name"], ["Period", "period"], ["Task Type", "task_type"], ["Report Format", "report_format"]].map(([label, key]) => (
                <div key={key}>
                  <label style={styles.label}>{label}</label>
                  {key === "task_type" ? (
                    <select style={styles.input} value={taskForm[key]} onChange={e => setTaskForm(p => ({ ...p, [key]: e.target.value }))}>
                      <option value="full_report">Full Report</option>
                      <option value="variance_analysis">Variance Analysis</option>
                      <option value="gaap_review">GAAP Review</option>
                      <option value="ifrs_review">IFRS Review</option>
                    </select>
                  ) : key === "report_format" ? (
                    <select style={styles.input} value={taskForm[key]} onChange={e => setTaskForm(p => ({ ...p, [key]: e.target.value }))}>
                      <option value="board">Board</option>
                      <option value="investor">Investor</option>
                      <option value="internal">Internal</option>
                      <option value="audit">Audit</option>
                    </select>
                  ) : (
                    <input style={styles.input} value={taskForm[key]} onChange={e => setTaskForm(p => ({ ...p, [key]: e.target.value }))} />
                  )}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16 }}>
              <label style={styles.label}>Task Description</label>
              <input style={styles.input} value={taskForm.task_description} onChange={e => setTaskForm(p => ({ ...p, task_description: e.target.value }))} />
            </div>
            <div style={{ marginTop: 16 }}>
              <label style={styles.label}>Financial Data (JSON)</label>
              <textarea style={styles.textarea} value={taskForm.raw_financial_data} onChange={e => setTaskForm(p => ({ ...p, raw_financial_data: e.target.value }))} rows={12} />
            </div>
            {error && <div style={{ background: "rgba(248,113,113,0.1)", border: "1px solid rgba(248,113,113,0.3)", borderRadius: 8, padding: 12, color: COLORS.red, fontSize: 13, marginTop: 16 }}>Error: {error}</div>}
            <button style={{ ...styles.btnPrimary, marginTop: 20, opacity: loading ? 0.6 : 1 }} onClick={submitTask} disabled={loading}>
              {loading ? "Submitting…" : "▶ Run AI CFO Pipeline"}
            </button>
          </div>
        </div>
      )}

      {/* ── Pipeline Status ── */}
      {tab === "status" && (
        <div>
          {!taskId && <div style={{ ...styles.card, color: COLORS.muted }}>No task running. Submit a task first.</div>}
          {taskId && (
            <>
              <div style={styles.card}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase" }}>Pipeline: {taskId}</div>
                  <span style={styles.tag(taskStatus?.status === "complete" ? COLORS.green : taskStatus?.status === "error" ? COLORS.red : COLORS.amber)}>
                    {taskStatus?.status?.toUpperCase() || "RUNNING"}
                  </span>
                </div>
                <PipelineStatus statuses={taskStatus?.agent_statuses} />
              </div>

              {/* KPIs */}
              {taskStatus?.kpi_metrics && (
                <div style={{ ...styles.grid3, marginBottom: 20 }}>
                  <KpiCard label="Gross Margin" value={taskStatus.kpi_metrics.gross_margin_pct?.toFixed(1)} unit="%" color={COLORS.green} />
                  <KpiCard label="EBITDA Margin" value={taskStatus.kpi_metrics.ebitda_margin_pct?.toFixed(1)} unit="%" color={COLORS.amber} />
                  <KpiCard label="Current Ratio" value={taskStatus.kpi_metrics.current_ratio?.toFixed(2)} color={COLORS.blue} />
                  <KpiCard label="Diluted EPS" value={taskStatus.kpi_metrics.diluted_eps?.toFixed(2)} unit="" color={COLORS.cyan} />
                  <KpiCard label="Net Debt" value={"$" + ((taskStatus.kpi_metrics.net_debt || 0) / 1e6).toFixed(1) + "M"} color={COLORS.purple} />
                  <KpiCard label="DSO Days" value={taskStatus.kpi_metrics.dso_days?.toFixed(0)} color={COLORS.muted} />
                </div>
              )}

              {/* GAAP/IFRS */}
              <div style={styles.grid2}>
                <ComplianceTable results={taskStatus?.gaap_results} title="US GAAP — 12 ASC Standards" />
                <ComplianceTable results={taskStatus?.ifrs_results} title="IFRS — 12 IASB Standards" />
              </div>

              {/* HITL Approval */}
              {taskStatus?.status === "awaiting_approval" && (
                <div style={{ ...styles.glowCard, borderColor: "rgba(251,191,36,0.3)", marginTop: 20 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.amber, marginBottom: 16 }}>⚠ Human Approval Required</div>
                  <div style={{ fontSize: 13, color: "#94A3B8", marginBottom: 16 }}>
                    The pipeline has paused pending CFO review. Approval triggers:
                    {taskStatus.approval_triggers?.map((t, i) => (
                      <div key={i} style={{ marginTop: 8, padding: "8px 12px", background: "rgba(0,0,0,0.3)", borderRadius: 6, fontSize: 12 }}>
                        <span style={{ color: t.severity === "critical" ? COLORS.red : COLORS.amber, fontWeight: 600 }}>{t.severity?.toUpperCase()}</span>
                        {" — "}{t.message}
                      </div>
                    ))}
                  </div>
                  <div style={styles.grid2}>
                    <div>
                      <label style={styles.label}>Decision</label>
                      <select style={styles.input} value={approvalForm.decision} onChange={e => setApprovalForm(p => ({ ...p, decision: e.target.value }))}>
                        <option value="approved">Approve</option>
                        <option value="rejected">Reject</option>
                      </select>
                    </div>
                    <div>
                      <label style={styles.label}>Approved By</label>
                      <input style={styles.input} value={approvalForm.approved_by} onChange={e => setApprovalForm(p => ({ ...p, approved_by: e.target.value }))} />
                    </div>
                  </div>
                  <div style={{ marginTop: 12 }}>
                    <label style={styles.label}>CFO Notes (include variance explanation + GAAP/IFRS disclosure plan)</label>
                    <textarea style={styles.textarea} value={approvalForm.feedback} onChange={e => setApprovalForm(p => ({ ...p, feedback: e.target.value }))} rows={4} />
                  </div>
                  <button style={{ ...styles.btnPrimary, marginTop: 12 }} onClick={submitApproval}>Submit CFO Decision</button>
                </div>
              )}

              {/* Final Report */}
              {taskStatus?.report && (
                <div style={{ ...styles.card, marginTop: 20 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "#94A3B8", marginBottom: 16, textTransform: "uppercase" }}>Board Report</div>
                  <pre style={{ whiteSpace: "pre-wrap", fontSize: 13, lineHeight: 1.7, color: "#E2E8F0" }}>{taskStatus.report}</pre>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* ── GAAP/IFRS Debate ── */}
      {tab === "debate" && (
        <div>
          <div style={styles.card}>
            <div style={{ fontSize: 14, fontWeight: 600, color: "#94A3B8", marginBottom: 20, textTransform: "uppercase" }}>3-Round IFRS vs GAAP Agentic Debate</div>
            <div style={styles.grid3}>
              {[["Company", "company_name"], ["Period", "period"], ["Jurisdiction", "jurisdiction"], ["Exchange", "listing_exchange"], ["Industry", "industry"]].map(([label, key]) => (
                <div key={key}>
                  <label style={styles.label}>{label}</label>
                  <input style={styles.input} value={debateForm[key]} onChange={e => setDebateForm(p => ({ ...p, [key]: e.target.value }))} />
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16 }}>
              <label style={styles.label}>Financial Data (JSON)</label>
              <textarea style={styles.textarea} value={debateForm.financial_data} onChange={e => setDebateForm(p => ({ ...p, financial_data: e.target.value }))} rows={8} />
            </div>
            <button style={{ ...styles.btnPrimary, marginTop: 20, opacity: debateLoading ? 0.6 : 1 }} onClick={runDebate} disabled={debateLoading}>
              {debateLoading ? "Running 3-Round Debate…" : "⚔ Run IFRS vs GAAP Debate"}
            </button>
          </div>

          {debateResult && (
            <div style={{ display: "grid", gap: 20 }}>
              {[
                { key: "round_1_ifrs_advocate", title: "Round 1 — IFRS Advocate", color: COLORS.blue },
                { key: "round_2_gaap_advocate", title: "Round 2 — GAAP Advocate", color: COLORS.amber },
                { key: "round_3_arbiter_verdict", title: "Round 3 — Independent Arbiter (VERDICT)", color: COLORS.cyan },
              ].map(({ key, title, color }) => (
                <div key={key} style={{ ...styles.card, borderLeft: `3px solid ${color}` }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color, marginBottom: 16 }}>{title}</div>
                  <pre style={{ whiteSpace: "pre-wrap", fontSize: 13, lineHeight: 1.7, color: "#E2E8F0" }}>{debateResult[key]}</pre>
                </div>
              ))}

              <div style={styles.grid2}>
                <ComplianceTable results={debateResult.gaap_summary} title="GAAP Compliance Summary" />
                <ComplianceTable results={debateResult.ifrs_summary} title="IFRS Compliance Summary" />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
