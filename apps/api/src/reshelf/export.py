"""Excel export of one scenario result (war plan 6.2). Every sheet carries the simulated data label."""

from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from reshelf.api_models import KpiOut, ScenarioResult

LABEL = "Simulated data. Every figure comes from a seeded synthetic world."
COMPARED = "Compared against the greedy baseline (compliant plan)."


def _sheet(wb: Workbook, title: str, header: list[str], rows: list[list[object]]) -> Worksheet:
    ws: Worksheet = wb.create_sheet(title)
    ws.append([LABEL])
    ws.append(header)
    for cell in ws[2]:
        cell.font = Font(bold=True)
    for row in rows:
        ws.append(row)
    ws.freeze_panes = "A3"
    for index, name in enumerate(header, start=1):
        width = max([len(name)] + [len(str(r[index - 1])) for r in rows[:200]]) + 2
        ws.column_dimensions[get_column_letter(index)].width = min(width, 48)
    return ws


def _kpi_rows(opt: KpiOut, raw: KpiOut, ok: KpiOut) -> list[list[object]]:
    return [
        ["Value recovered (EUR)", opt.value_recovered, raw.value_recovered, ok.value_recovered],
        ["Units allocated", opt.units_allocated, raw.units_allocated, ok.units_allocated],
        ["Units destroyed", opt.units_destroyed, raw.units_destroyed, ok.units_destroyed],
        ["Brand risk index", opt.brand_risk_index, raw.brand_risk_index, ok.brand_risk_index],
        ["SKU score", opt.score, raw.score, ok.score],
    ]


def build_workbook(name: str, result: ScenarioResult) -> bytes:
    wb = Workbook()
    summary = wb.active
    assert summary is not None
    wb.remove(summary)
    b = result.baseline
    _sheet(
        wb,
        "Summary",
        ["Measure", "Optimizer", "Greedy baseline (raw)", "Greedy baseline (compliant)"],
        [
            ["Scenario", name, "", ""],
            ["Comparison", COMPARED, "", ""],
            ["Solver status", result.solve.status, "", ""],
            ["MIP gap", result.solve.mip_gap if result.solve.mip_gap is not None else "", "", ""],
            ["Solve time (s)", round(result.solve.time_s, 2), "", ""],
            *_kpi_rows(result.optimizer, b.raw, b.compliant),
        ],
    )
    _sheet(
        wb,
        "Allocation",
        ["Line", "Lot", "Channel", "Units", "Lot supply", "Net value (EUR)"],
        [
            [x.line, x.lot, x.channel, x.quantity, x.lot_supply, x.net_value_eur]
            for x in result.lines
        ],
    )
    _sheet(
        wb,
        "Baseline audit",
        ["Rule", "Violated instances", "Excess"],
        [[rule, a.count, a.excess] for rule, a in sorted(b.audit.items())],
    )
    _sheet(
        wb,
        "Rule trace",
        ["Line", "Units", "Binding rules", "Blocked channels"],
        [
            [
                t.line,
                t.quantity,
                ", ".join(f"{r.instance} (slack {r.slack:g})" for r in t.binding),
                ", ".join(f"{c.channel}: {'+'.join(c.reasons)}" for c in t.blocked),
            ]
            for t in result.trace.lines
        ],
    )
    _sheet(
        wb,
        "Rule cost",
        ["Rule instance", "Change", "Cost (EUR)", "Units destroyed by the rule", "Status"],
        [
            [c.instance, c.mode, c.cost_eur, c.units_destroyed_by_rule, c.status]
            for c in result.counterfactuals
        ],
    )
    out = BytesIO()
    wb.save(out)
    return out.getvalue()
