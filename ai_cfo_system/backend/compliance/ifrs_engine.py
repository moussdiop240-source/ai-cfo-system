"""
IFRS COMPLIANCE ENGINE — 12 IASB Standards.
DETERMINISTIC — ZERO LLM. Every check is rule-based code.
"""
from typing import Any, Dict


class IFRSEngine:
    """12 IASB IAS/IFRS standards — deterministic compliance checks."""

    def check_all(
        self,
        data: Dict[str, Any],
        kpis: Dict[str, float],
        variance: Dict[str, Any],
        runway: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "ias1":   self.presentation(data),
            "ias2":   self.inventories(data),
            "ias7":   self.cash_flows(data),
            "ias12":  self.taxes(data, kpis),
            "ias16":  self.ppe(data),
            "ias33":  self.eps(data, kpis),
            "ias36":  self.impairment(data),
            "ias37":  self.provisions(data),
            "ias38":  self.intangibles(data),
            "ifrs9":  self.credit_losses(data, kpis),
            "ifrs15": self.revenue(data),
            "ifrs16": self.leases(data, kpis),
        }

    def presentation(self, data: Dict) -> Dict:
        """IAS 1: Presentation of Financial Statements — OCI + comparatives required."""
        standard = "IAS 1"
        issues = []

        has_oci = data.get("other_comprehensive_income") is not None
        if not has_oci and (
            float(data.get("unrealized_gains_losses", 0)) != 0
            or float(data.get("fx_translation", 0)) != 0
            or float(data.get("pension_remeasurement", 0)) != 0
        ):
            issues.append(
                "Other Comprehensive Income (OCI) items exist but statement of OCI not presented "
                "(IAS 1.81: profit/loss + OCI must be presented)"
            )

        if not data.get("comparative_period_presented"):
            issues.append(
                "Comparative prior period figures not presented — required by IAS 1.38"
            )

        status = "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "finding": "; ".join(issues) if issues else "Financial statement presentation complies with IAS 1",
            "key_rule": "IAS 1 requires statement of profit or loss AND OCI, plus minimum 2 years comparative",
        }

    def inventories(self, data: Dict) -> Dict:
        """IAS 2: Inventories — LIFO is STRICTLY PROHIBITED under IFRS."""
        standard = "IAS 2"
        issues = []

        inventory_method = data.get("inventory_cost_method", "fifo").upper()
        if inventory_method == "LIFO":
            issues.append(
                "LIFO inventory method is STRICTLY PROHIBITED under IFRS IAS 2.25 — "
                "must restate to FIFO or weighted average cost"
            )

        inventory = float(data.get("inventory", 0))
        nrv = float(data.get("net_realizable_value", inventory))
        if inventory > 0 and nrv < inventory:
            write_down = round(inventory - nrv, 2)
            issues.append(
                f"Inventory NRV ${nrv:,.0f} is below cost ${inventory:,.0f} — "
                f"write-down of ${write_down:,.0f} required (IAS 2.9: lower of cost and NRV)"
            )

        status = "NON_COMPLIANT" if inventory_method == "LIFO" else (
            "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        )
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "inventory_method": inventory_method,
            "finding": "; ".join(issues) if issues else f"Inventory ${inventory:,.0f} valued at lower of cost and NRV",
            "key_difference_from_gaap": "LIFO PROHIBITED under IFRS | LIFO PERMITTED under GAAP ASC 330",
        }

    def cash_flows(self, data: Dict) -> Dict:
        """IAS 7: Cash Flows — interest paid is a POLICY CHOICE (Operating or Financing)."""
        standard = "IAS 7"
        issues = []

        policy = data.get("interest_cash_flow_classification", "")
        if not policy:
            issues.append(
                "Interest paid / received classification not documented — "
                "IAS 7.31 requires policy disclosure (policy choice: Operating or Financing)"
            )

        if not data.get("cash_flow_policy_consistent"):
            issues.append(
                "Cash flow classification policy must be applied consistently (IAS 7.1)"
            )

        status = "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "finding": "; ".join(issues) if issues else f"Cash flow classification policy documented: '{policy}'",
            "key_difference_from_gaap": "IFRS: interest paid = POLICY CHOICE | GAAP ASC 230: MUST be Operating",
        }

    def taxes(self, data: Dict, kpis: Dict) -> Dict:
        """IAS 12: Income Taxes — DTL on goodwill, temporary difference approach."""
        standard = "IAS 12"
        issues = []

        goodwill = float(data.get("goodwill", 0))
        dtl_goodwill = float(data.get("deferred_tax_liability_goodwill", 0))

        if goodwill > 0 and dtl_goodwill == 0:
            issues.append(
                f"Goodwill ${goodwill:,.0f} — IAS 12.21A: deferred tax liability on goodwill "
                "may be required depending on business combination accounting"
            )

        dta = float(data.get("deferred_tax_asset", 0))
        net_income = float(data.get("net_income", 0))
        if dta > 0 and net_income < 0:
            issues.append(
                f"DTA ${dta:,.0f} with net losses — IAS 12.34: recognize DTA only to extent "
                "probable that sufficient future taxable profit will be available"
            )

        status = "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "finding": "; ".join(issues) if issues else "Deferred tax balances assessed per IAS 12",
            "key_difference_from_gaap": "IAS 12: 'probable' threshold | ASC 740: 'more likely than not' threshold",
        }

    def ppe(self, data: Dict) -> Dict:
        """IAS 16: Property, Plant & Equipment — revaluation model option (not in GAAP)."""
        standard = "IAS 16"
        issues = []

        ppe_net = float(data.get("ppe_net", 0))
        ppe_measurement_model = data.get("ppe_measurement_model", "cost")

        if ppe_measurement_model == "revaluation":
            last_revaluation = data.get("last_revaluation_date")
            if not last_revaluation:
                issues.append(
                    "PPE revaluation model selected — IAS 16.34: revaluations must be "
                    "made with sufficient regularity to ensure carrying amount does not "
                    "differ materially from fair value"
                )

        dep_method = data.get("depreciation_method", "")
        if not dep_method:
            issues.append("Depreciation method not documented — required disclosure per IAS 16.73")

        status = "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "ppe_net": ppe_net,
            "measurement_model": ppe_measurement_model,
            "finding": "; ".join(issues) if issues else f"PP&E ${ppe_net:,.0f} — {ppe_measurement_model} model applied",
            "key_difference_from_gaap": "IFRS: REVALUATION MODEL option | GAAP: cost model ONLY",
        }

    def eps(self, data: Dict, kpis: Dict) -> Dict:
        """IAS 33: EPS — similar to ASC 260, required for listed entities."""
        standard = "IAS 33"
        issues = []

        basic_eps = kpis.get("basic_eps")
        diluted_eps = kpis.get("diluted_eps")

        if data.get("publicly_listed") and basic_eps is None:
            issues.append(
                "Basic EPS not presented — IAS 33.66 requires EPS on face of income statement for listed entities"
            )

        if data.get("publicly_listed") and diluted_eps is None:
            issues.append(
                "Diluted EPS not presented — required if dilutive instruments exist (IAS 33.31)"
            )

        status = "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "finding": "; ".join(issues) if issues else f"EPS: Basic ${basic_eps}, Diluted ${diluted_eps}",
        }

    def impairment(self, data: Dict) -> Dict:
        """IAS 36: Impairment — CGU-level testing; reversal PERMITTED (unlike GAAP)."""
        standard = "IAS 36"
        issues = []

        goodwill = float(data.get("goodwill", 0))
        intangibles_indefinite = float(data.get("intangibles_indefinite_life", 0))

        if goodwill > 0 and not data.get("impairment_test_performed"):
            issues.append(
                f"Goodwill ${goodwill:,.0f} — IAS 36.96: annual impairment test required "
                "(regardless of impairment indicators)"
            )

        if intangibles_indefinite > 0 and not data.get("intangibles_impairment_test_performed"):
            issues.append(
                f"Indefinite-life intangibles ${intangibles_indefinite:,.0f} — "
                "annual impairment test required (IAS 36.10)"
            )

        cgu_level = data.get("impairment_tested_at_cgu_level")
        if cgu_level is False:
            issues.append(
                "Impairment tested at wrong level — IAS 36.65: goodwill allocated to CGUs, "
                "tested at CGU (or group of CGUs) level"
            )

        status = "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "finding": "; ".join(issues) if issues else "Impairment testing assessed per IAS 36",
            "key_difference_from_gaap": "IFRS IAS 36: impairment REVERSAL PERMITTED | GAAP ASC 350: NO reversal",
        }

    def provisions(self, data: Dict) -> Dict:
        """IAS 37: Provisions — >50% probable threshold (lower than GAAP ~75%)."""
        standard = "IAS 37"
        issues = []

        contingencies = data.get("contingent_liabilities", [])
        for item in contingencies:
            prob = float(item.get("probability", 0))
            amount = float(item.get("estimated_amount", 0))
            accrued = float(item.get("accrued_amount", 0))

            if prob > 0.50 and accrued == 0 and amount > 0:
                issues.append(
                    f"Contingency '{item.get('description', 'Unknown')}' at {prob*100:.0f}% — "
                    f"provision of ${amount:,.0f} required under IAS 37.14 (>50% probable + reliably estimable)"
                )

        restructuring = float(data.get("restructuring_provision", 0))
        restructuring_plan = data.get("restructuring_formal_plan")
        if restructuring > 0 and not restructuring_plan:
            issues.append(
                f"Restructuring provision ${restructuring:,.0f} without formal plan — "
                "IAS 37.72: constructive obligation requires formal plan communicated to affected parties"
            )

        status = "NON_COMPLIANT" if any("required" in i for i in issues) else (
            "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        )
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "finding": "; ".join(issues) if issues else "Provisions assessed per IAS 37",
            "key_difference_from_gaap": "IFRS >50% probable | GAAP ~75% probable — IFRS recognizes earlier",
        }

    def intangibles(self, data: Dict) -> Dict:
        """IAS 38: Intangible Assets — development costs MUST be capitalized if criteria met."""
        standard = "IAS 38"
        issues = []

        rd_expense = float(data.get("rd_expense", 0))
        dev_costs_capitalized = float(data.get("development_costs_capitalized", 0))
        has_qualifying_dev = data.get("qualifying_development_projects", False)

        if rd_expense > 0 and has_qualifying_dev and dev_costs_capitalized == 0:
            issues.append(
                f"R&D expense ${rd_expense:,.0f} with qualifying development projects — "
                "IAS 38.57: development costs MUST be capitalized if all 6 criteria met: "
                "(technical feasibility, intention, ability, future economic benefits, "
                "adequate resources, reliable measurement)"
            )

        if dev_costs_capitalized > 0:
            amortization_period = data.get("dev_costs_amortization_years")
            if not amortization_period:
                issues.append(
                    f"Development costs ${dev_costs_capitalized:,.0f} capitalized — "
                    "amortization period and method must be disclosed (IAS 38.118)"
                )

        status = "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "rd_expense": rd_expense,
            "dev_costs_capitalized": dev_costs_capitalized,
            "finding": "; ".join(issues) if issues else "Intangible asset policy assessed per IAS 38",
            "key_difference_from_gaap": "IFRS: dev costs CAPITALIZED if criteria met | GAAP ASC 730: ALL R&D expensed",
        }

    def credit_losses(self, data: Dict, kpis: Dict) -> Dict:
        """IFRS 9: Financial Instruments — 3-stage ECL (Expected Credit Loss) model."""
        standard = "IFRS 9"
        issues = []

        ar = float(data.get("accounts_receivable", 0))
        ecl_stage1 = float(data.get("ecl_stage1_allowance", 0))
        ecl_stage2 = float(data.get("ecl_stage2_allowance", 0))
        ecl_stage3 = float(data.get("ecl_stage3_allowance", 0))
        total_ecl = ecl_stage1 + ecl_stage2 + ecl_stage3

        if ar > 0 and total_ecl == 0:
            issues.append(
                f"AR ${ar:,.0f} with no ECL allowance — "
                "IFRS 9.5.5: 3-stage ECL model requires expected credit loss recognition "
                "(Stage 1: 12-month ECL | Stage 2/3: lifetime ECL)"
            )

        loans = float(data.get("loans_receivable", 0))
        if loans > 0 and total_ecl == 0:
            issues.append(
                f"Loans ${loans:,.0f} — IFRS 9 ECL assessment required at origination (Stage 1)"
            )

        dso = kpis.get("dso_days", 0)
        if dso > 90 and total_ecl < ar * 0.05:
            issues.append(
                f"DSO {dso} days suggests Stage 2/3 migration — "
                "review whether lifetime ECL applies (IFRS 9.5.5.3: significant increase in credit risk)"
            )

        status = "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "ecl_total": total_ecl,
            "stages": {"stage1": ecl_stage1, "stage2": ecl_stage2, "stage3": ecl_stage3},
            "finding": "; ".join(issues) if issues else f"ECL allowance ${total_ecl:,.0f} assessed across 3 stages",
            "key_difference_from_gaap": "IFRS 9 ECL (3-stage, forward-looking) | GAAP ASC 326 CECL (lifetime from day 1)",
        }

    def revenue(self, data: Dict) -> Dict:
        """IFRS 15: Revenue — converged with ASC 606, minor differences remain."""
        standard = "IFRS 15"
        issues = []

        revenue = float(data.get("revenue", 0))
        deferred_revenue = float(data.get("deferred_revenue", 0))
        contract_assets = float(data.get("contract_assets", 0))
        rev_policy = data.get("revenue_recognition_policy", "")

        if revenue > 0 and not rev_policy:
            issues.append(
                "Revenue recognition policy not disclosed — "
                "IFRS 15.110: disaggregation of revenue + description of performance obligations required"
            )

        if deferred_revenue > revenue * 0.25:
            issues.append(
                f"Contract liabilities (deferred revenue) ${deferred_revenue:,.0f} are >25% of revenue — "
                "IFRS 15.116: significant remaining performance obligation disclosure required"
            )

        status = "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "finding": "; ".join(issues) if issues else f"Revenue ${revenue:,.0f} recognized per IFRS 15 (converged with ASC 606)",
            "key_difference_from_gaap": "IFRS 15 and ASC 606 are largely converged; minor differences in licenses and variable consideration",
        }

    def leases(self, data: Dict, kpis: Dict) -> Dict:
        """IFRS 16: Leases — SINGLE model (all leases treated as finance); EBITDA impact."""
        standard = "IFRS 16"
        issues = []

        rou_assets = float(data.get("rou_assets", 0))
        lease_liability = float(data.get("lease_liability", 0))
        operating_leases_off_bs = float(data.get("operating_leases_not_capitalized", 0))

        if operating_leases_off_bs > 0:
            issues.append(
                f"Operating leases ${operating_leases_off_bs:,.0f} not on balance sheet — "
                "IFRS 16: ALL leases (except short-term <12mo and low-value) must be capitalized"
            )

        op_lease_expense = float(data.get("operating_lease_expense", 0))
        if op_lease_expense > 0 and rou_assets == 0:
            issues.append(
                f"Operating lease expense ${op_lease_expense:,.0f} recorded but no ROU asset — "
                "review IFRS 16 recognition criteria"
            )

        ebitda_uplift = round(op_lease_expense, 2)

        status = "NON_COMPLIANT" if operating_leases_off_bs > 0 else (
            "DISCLOSURE_REQUIRED" if issues else "COMPLIANT"
        )
        return {
            "standard": standard,
            "status": status,
            "issues": issues,
            "rou_assets": rou_assets,
            "lease_liability": lease_liability,
            "ebitda_uplift_vs_gaap": ebitda_uplift,
            "finding": "; ".join(issues) if issues else (
                f"ROU assets ${rou_assets:,.0f} — IFRS 16 single model applied; "
                f"EBITDA ~${ebitda_uplift:,.0f} higher vs GAAP ASC 842 dual model"
            ),
            "key_difference_from_gaap": (
                "IFRS 16: SINGLE model — ALL leases on BS, lease expense → D&A + interest → EBITDA HIGHER | "
                "GAAP ASC 842: DUAL model — operating leases in SG&A → EBITDA LOWER"
            ),
        }
