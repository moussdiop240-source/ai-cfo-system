"""
GAAP COMPLIANCE ENGINE — 12 FASB ASC Standards.
DETERMINISTIC — ZERO LLM. Every check is rule-based code.
"""
from typing import Dict, Any, Optional
from datetime import datetime


class GAAPEngine:
    """12 FASB ASC standards — deterministic compliance checks."""

    def check_all(
        self,
        data: Dict[str, Any],
        kpis: Dict[str, float],
        variance: Dict[str, Any],
        runway: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "asc205": self.going_concern(data, kpis, runway),
            "asc230": self.cash_flows(data),
            "asc260": self.eps(data, kpis),
            "asc280": self.segments(data),
            "asc310": self.receivables(data, kpis),
            "asc350": self.goodwill(data),
            "asc450": self.contingencies(data),
            "asc606": self.revenue_recognition(data),
            "asc740": self.income_taxes(data),
            "asc820": self.fair_value(data),
            "asc842": self.leases(data),
            "sab99":  self.materiality(data, variance),
        }

    def going_concern(self, data: Dict, kpis: Dict, runway: Dict) -> Dict:
        """ASC 205-40: Going Concern — 12 months from financial statement issuance."""
        standard = "ASC 205-40"
        issues = []

        runway_months = runway.get("runway_months", 999)
        if runway_months < 12:
            issues.append(f"Cash runway {runway_months:.1f} months is within 12-month going concern window")

        current_ratio = kpis.get("current_ratio", 99)
        if current_ratio < 1.0:
            issues.append(f"Current ratio {current_ratio} below 1.0 — substantial doubt indicator")

        net_income = float(data.get("net_income", 0))
        if net_income < 0:
            issues.append(f"Negative net income ${net_income:,.0f} — recurring losses indicator")

        status = "NON_COMPLIANT" if len(issues) >= 2 else ("DISCLOSURE_REQUIRED" if issues else "COMPLIANT")

        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "finding": (
                f"Going concern disclosure required: {'; '.join(issues)}"
                if issues else "No going concern indicators identified"
            ),
            "required_disclosure": status in ("NON_COMPLIANT", "DISCLOSURE_REQUIRED"),
            "disclosure_note": (
                "Management must evaluate whether conditions raise substantial doubt about the "
                "entity's ability to continue as a going concern within 12 months from the "
                "date the financial statements are issued (ASC 205-40-50-1)."
            ) if issues else None,
        }

    def cash_flows(self, data: Dict) -> Dict:
        """ASC 230: Cash Flows — interest paid and received MUST be classified as Operating."""
        standard = "ASC 230"
        issues = []

        interest_classification = data.get("interest_cash_flow_classification", "operating")
        if interest_classification.lower() != "operating":
            issues.append(
                f"Interest paid classified as '{interest_classification}' — "
                "ASC 230 requires interest paid to be Operating activities"
            )

        taxes_classification = data.get("taxes_paid_cash_flow_classification", "operating")
        if taxes_classification.lower() != "operating":
            issues.append(
                f"Income taxes paid classified as '{taxes_classification}' — "
                "ASC 230 requires taxes paid to be Operating (unless specific ID to financing)"
            )

        status = "NON_COMPLIANT" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "finding": "; ".join(issues) if issues else "Cash flow classifications comply with ASC 230",
            "key_rule": "Interest paid = Operating (unlike IFRS where it's a policy choice)",
        }

    def eps(self, data: Dict, kpis: Dict) -> Dict:
        """ASC 260: EPS — both basic and diluted must be presented."""
        standard = "ASC 260"
        issues = []

        basic_eps = kpis.get("basic_eps")
        diluted_eps = kpis.get("diluted_eps")

        if basic_eps is None:
            issues.append("Basic EPS not calculated — required for public companies (ASC 260-10-45-2)")

        if diluted_eps is None:
            issues.append("Diluted EPS not calculated — required when dilutive securities exist")

        has_options = float(data.get("dilutive_options", 0)) > 0
        has_convertibles = float(data.get("convertible_debt", 0)) > 0
        if (has_options or has_convertibles) and diluted_eps == basic_eps:
            issues.append(
                "Dilutive securities exist but basic EPS equals diluted EPS — verify treasury stock method"
            )

        status = "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "finding": "; ".join(issues) if issues else f"EPS compliant: Basic ${basic_eps}, Diluted ${diluted_eps}",
            "basic_eps": basic_eps,
            "diluted_eps": diluted_eps,
        }

    def segments(self, data: Dict) -> Dict:
        """ASC 280: Segment Reporting — 10% revenue/profit/asset threshold."""
        standard = "ASC 280"
        issues = []

        segments = data.get("segments", [])
        total_revenue = float(data.get("revenue", 1))

        reportable = []
        for seg in segments:
            seg_rev = float(seg.get("revenue", 0))
            seg_pct = round(seg_rev / total_revenue * 100, 1) if total_revenue else 0
            if seg_pct >= 10:
                reportable.append(f"{seg.get('name', 'Unknown')}: {seg_pct}%")

        if len(segments) > 1 and not data.get("segment_disclosures_present"):
            issues.append(
                f"Multiple operating segments identified — segment disclosures required (ASC 280-10-50)"
            )

        status = "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "reportable_segments": reportable,
            "finding": "; ".join(issues) if issues else "Segment reporting requirements assessed",
        }

    def receivables(self, data: Dict, kpis: Dict) -> Dict:
        """ASC 310 / ASC 326: Receivables — CECL (Current Expected Credit Losses)."""
        standard = "ASC 310 / ASC 326 (CECL)"
        issues = []

        ar = float(data.get("accounts_receivable", 0))
        allowance = float(data.get("allowance_for_credit_losses", 0))
        revenue = float(data.get("revenue", 1))

        if ar > 0 and allowance == 0:
            issues.append(
                "Accounts receivable has no allowance for credit losses — "
                "CECL lifetime expected losses must be recognized (ASC 326-20)"
            )

        if ar > 0:
            allowance_pct = round(allowance / ar * 100, 1)
            if allowance_pct < 1.0 and ar / revenue > 0.1:
                issues.append(
                    f"Allowance {allowance_pct}% of AR appears low — "
                    "CECL requires forward-looking lifetime expected credit losses"
                )

        dso = kpis.get("dso_days", 0)
        if dso > 90:
            issues.append(f"DSO of {dso} days suggests collection risk — review CECL estimate adequacy")

        status = "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "ar_balance": ar,
            "allowance": allowance,
            "finding": "; ".join(issues) if issues else f"CECL allowance of ${allowance:,.0f} assessed ({round(allowance/ar*100,1) if ar else 0}% of AR)",
        }

    def goodwill(self, data: Dict) -> Dict:
        """ASC 350: Goodwill — annual impairment test, NO reversal permitted."""
        standard = "ASC 350"
        issues = []

        goodwill = float(data.get("goodwill", 0))
        last_impairment_test = data.get("goodwill_impairment_test_date")
        impairment_reversal = data.get("goodwill_impairment_reversal", 0)

        if goodwill > 0:
            if not last_impairment_test:
                issues.append(
                    f"Goodwill ${goodwill:,.0f} — annual impairment test date not documented (ASC 350-20-35)"
                )

            if float(impairment_reversal) > 0:
                issues.append(
                    "Goodwill impairment reversal detected — PROHIBITED under ASC 350 "
                    "(unlike IFRS IAS 36 which permits reversal)"
                )

        status = "NON_COMPLIANT" if any("reversal" in i for i in issues) else (
            "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        )
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "goodwill_balance": goodwill,
            "finding": "; ".join(issues) if issues else (
                f"Goodwill ${goodwill:,.0f} — annual impairment test required" if goodwill > 0 else "No goodwill"
            ),
            "key_difference_from_ifrs": "GAAP: NO impairment reversal | IFRS IAS 36: reversal PERMITTED",
        }

    def contingencies(self, data: Dict) -> Dict:
        """ASC 450: Contingencies — ~75% 'probable' threshold for accrual."""
        standard = "ASC 450"
        issues = []

        contingencies = data.get("contingent_liabilities", [])
        for item in contingencies:
            prob = float(item.get("probability", 0))
            amount = float(item.get("estimated_amount", 0))
            accrued = float(item.get("accrued_amount", 0))

            if prob >= 0.75 and accrued == 0 and amount > 0:
                issues.append(
                    f"Contingency '{item.get('description', 'Unknown')}' "
                    f"at {prob*100:.0f}% probability ${amount:,.0f} — "
                    "accrual required (ASC 450-20-25-2: probable + estimable)"
                )
            elif 0.50 <= prob < 0.75 and amount > 0:
                issues.append(
                    f"Contingency at {prob*100:.0f}% probability — "
                    "disclosure required (note: IFRS IAS 37 requires accrual at >50%)"
                )

        status = "NON_COMPLIANT" if any("accrual required" in i for i in issues) else (
            "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        )
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "finding": "; ".join(issues) if issues else "Contingency assessment complete",
            "key_difference_from_ifrs": "GAAP ~75% probable | IFRS >50% probable (earlier recognition)",
        }

    def revenue_recognition(self, data: Dict) -> Dict:
        """ASC 606: Revenue — 5-step model compliance check."""
        standard = "ASC 606"
        issues = []

        deferred_revenue = float(data.get("deferred_revenue", 0))
        contract_assets   = float(data.get("contract_assets", 0))
        revenue = float(data.get("revenue", 0))

        rev_recognition_policy = data.get("revenue_recognition_policy", "")
        if revenue > 0 and not rev_recognition_policy:
            issues.append(
                "Revenue recognition policy not documented — "
                "ASC 606 requires disclosure of performance obligations, "
                "transaction price allocation, and timing of recognition"
            )

        if deferred_revenue > revenue * 0.20:
            issues.append(
                f"Deferred revenue ${deferred_revenue:,.0f} is >20% of revenue — "
                "review satisfaction of performance obligations (ASC 606-10-25-30)"
            )

        status = "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "deferred_revenue": deferred_revenue,
            "finding": "; ".join(issues) if issues else f"Revenue ${revenue:,.0f} recognized per ASC 606 5-step model",
            "five_steps": [
                "1. Identify the contract(s) with a customer",
                "2. Identify the performance obligations",
                "3. Determine the transaction price",
                "4. Allocate the transaction price",
                "5. Recognize revenue when (or as) obligation satisfied",
            ],
        }

    def income_taxes(self, data: Dict) -> Dict:
        """ASC 740: Income Taxes — DTA 'more likely than not' realizability."""
        standard = "ASC 740"
        issues = []

        dta = float(data.get("deferred_tax_asset", 0))
        valuation_allowance = float(data.get("valuation_allowance", 0))
        net_income = float(data.get("net_income", 0))
        effective_tax_rate = float(data.get("effective_tax_rate", 21.0))

        if dta > 0:
            va_pct = round(valuation_allowance / dta * 100, 1) if dta else 0
            if net_income < 0 and valuation_allowance == 0:
                issues.append(
                    f"DTA ${dta:,.0f} with no valuation allowance despite net losses — "
                    "ASC 740-10-30: assess 'more likely than not' realizability"
                )

        stat_rate = 0.21
        if abs(effective_tax_rate - stat_rate * 100) > 10:
            issues.append(
                f"Effective tax rate {effective_tax_rate:.1f}% differs materially from "
                f"21% statutory rate — rate reconciliation disclosure required (ASC 740-10-50-12)"
            )

        status = "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "dta": dta,
            "valuation_allowance": valuation_allowance,
            "finding": "; ".join(issues) if issues else f"DTA ${dta:,.0f} assessed for 'more likely than not' realizability",
            "key_rule": "DTA must be reduced by valuation allowance if not 'more likely than not' to be realized",
        }

    def fair_value(self, data: Dict) -> Dict:
        """ASC 820: Fair Value — L1/L2/L3 hierarchy disclosure."""
        standard = "ASC 820"
        issues = []

        investments = data.get("fair_value_investments", [])
        for inv in investments:
            level = inv.get("level")
            amount = float(inv.get("amount", 0))
            if level == 3 and amount > float(data.get("total_assets", 1)) * 0.05:
                issues.append(
                    f"Level 3 fair value measurement ${amount:,.0f} exceeds 5% of total assets — "
                    "expanded disclosure required (ASC 820-10-50: unobservable inputs, valuation technique)"
                )

            if level is None and amount > 0:
                issues.append(
                    f"Fair value measurement ${amount:,.0f} — fair value hierarchy level not disclosed"
                )

        status = "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "finding": "; ".join(issues) if issues else "Fair value hierarchy disclosures assessed",
            "hierarchy": {
                "L1": "Quoted prices in active markets (most reliable)",
                "L2": "Observable inputs other than L1",
                "L3": "Unobservable inputs (least reliable — expanded disclosure required)",
            },
        }

    def leases(self, data: Dict) -> Dict:
        """ASC 842: Leases — dual model (operating vs finance lease)."""
        standard = "ASC 842"
        issues = []

        rou_assets = float(data.get("rou_assets", 0))
        lease_liability = float(data.get("lease_liability", 0))
        operating_leases = float(data.get("operating_leases_not_capitalized", 0))

        if operating_leases > 0:
            issues.append(
                f"Operating leases ${operating_leases:,.0f} not capitalized — "
                "ASC 842 requires all leases >12 months on balance sheet as ROU asset + lease liability"
            )

        if rou_assets > 0 and lease_liability == 0:
            issues.append(
                "ROU assets recognized without corresponding lease liability — review ASC 842-20 measurement"
            )

        status = "NON_COMPLIANT" if operating_leases > 0 else ("DISCLOSURE_REQUIRED" if issues else "COMPLIANT")
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "rou_assets": rou_assets,
            "lease_liability": lease_liability,
            "finding": "; ".join(issues) if issues else f"ROU assets ${rou_assets:,.0f} and lease liabilities ${lease_liability:,.0f} properly recognized",
            "key_difference_from_ifrs": "GAAP: DUAL model (operating vs finance) | IFRS 16: SINGLE model (all finance-type)",
        }

    def materiality(self, data: Dict, variance: Dict) -> Dict:
        """SAB 99: Materiality — 5% threshold for financial statement items."""
        standard = "SAB 99 / ASC 250"
        issues = []

        material_items = variance.get("material_items", [])
        totals = variance.get("totals", {})
        var_pct = abs(totals.get("variance_pct", 0))

        if var_pct >= 5:
            issues.append(
                f"Total variance {var_pct:.1f}% meets SAB 99 5% materiality threshold — "
                "qualitative and quantitative analysis required"
            )

        for item in material_items:
            line = variance.get("line_items", {}).get(item, {})
            issues.append(
                f"Material variance in {item}: "
                f"${line.get('variance_abs', 0):,.0f} ({line.get('variance_pct', 0):.1f}%)"
            )

        status = "DISCLOSURE_REQUIRED" if var_pct >= 5 else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "material_items": material_items,
            "overall_variance_pct": var_pct,
            "finding": f"{len(material_items)} material variance items identified (≥5% threshold)" if material_items else "No material variances",
        }
