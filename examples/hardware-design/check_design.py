"""Check a synthetic design's arithmetic and references, not real hardware."""

import argparse
import hashlib
import json
from decimal import Decimal, DecimalException, InvalidOperation
from pathlib import Path

from firmware_model import policy_values


def inputs_digest(inputs):
    canonical = json.dumps(inputs, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def number(value, name, positive=False):
    if len(str(value)) > 64:
        raise ValueError(f"{name}: number representation is too long")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{name}: expected a finite number") from None
    if not result.is_finite() or result < 0 or (positive and result == 0):
        raise ValueError(f"{name}: invalid range")
    if result and not Decimal("1e-9") <= result <= Decimal("1e9"):
        raise ValueError(f"{name}: outside this teaching calculator's numeric range")
    return result


def text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}: expected nonempty text")
    return value


def text_list(value, name):
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name}: expected a nonempty list of text")
    return [text(item, name) for item in value]


def unique_index(rows, key, label):
    if not isinstance(rows, list) or not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{label}: expected a nonempty list of records")
    result = {text(row.get(key), label): row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"duplicate {label}")
    return result


def evaluate(inputs, design):
    if not isinstance(inputs, dict) or not isinstance(design, dict):
        raise ValueError("inputs and design must be records")
    if inputs["data_kind"] != "synthetic_teaching" or design["status"] != "draft":
        raise ValueError("this checker accepts synthetic drafts only")
    if design["input_snapshot"] != inputs["snapshot"]:
        raise ValueError("input snapshot changed; rebuild the design context")
    if design["input_sha256"] != inputs_digest(inputs):
        raise ValueError("input content changed; rebuild the design context")
    text(inputs["case_id"], "case ID")
    text(design["design_id"], "design ID")
    sources = unique_index(inputs["sources"], "ref", "source")
    requirements = unique_index(inputs["requirements"], "id", "requirement")
    radios = unique_index(inputs["radios"], "id", "radio")
    source_records = list(requirements.values()) + list(radios.values())
    source_records += [inputs["capacity"], inputs["power"], inputs["bom_base"], inputs["firmware_policy"]]
    if any(not isinstance(record, dict) for record in source_records):
        raise ValueError("every numeric input must be a versioned source record")
    used_refs = {text(record.get("source_ref"), "source reference") for record in source_records}
    cited_refs = set(text_list(design["source_refs"], "source references"))
    if not used_refs <= cited_refs or not cited_refs <= sources.keys():
        raise ValueError("missing or unknown versioned source reference")
    expected = {"R-SAMPLE", "R-UPLOAD", "R-LIFE", "R-BOM", "R-MECHANICAL", "R-MEASUREMENT"}
    if requirements.keys() != expected:
        raise ValueError("the W2 requirement set is incomplete or unsupported")
    verification = unique_index(design["verification_plan"], "id", "verification")
    for row in verification.values():
        text(row.get("method"), "verification method")
    if any(row["status"] != "planned" for row in verification.values()):
        raise ValueError("physical verification results are not part of this fixture")
    trace = unique_index(design["traceability"], "requirement_id", "traceability")
    if trace.keys() != requirements.keys():
        raise ValueError("every requirement needs a design and verification reference")
    sections = design["sections"]
    if not isinstance(sections, dict) or not sections:
        raise ValueError("design sections must map names to nonempty content")
    for name, content in sections.items():
        text(name, "section name")
        text(content, "section content")
    if not {"architecture", "power_schedule", "interfaces", "bom", "measurement", "firmware", "recovery"} <= sections.keys():
        raise ValueError("required design sections are missing")
    for row in trace.values():
        if text(row.get("design_ref"), "design reference") not in sections or text(row.get("verification_id"), "verification reference") not in verification:
            raise ValueError("unresolved design or verification reference")
    software_trace = unique_index(design["software_traceability"], "requirement_id", "software traceability")
    if software_trace.keys() != {"R-SAMPLE", "R-UPLOAD", "R-LIFE", "R-MEASUREMENT"}:
        raise ValueError("software allocation must cover sampling, upload, lifetime and measurement")
    software_expected = {"R-SAMPLE": ("firmware", "V-FIRMWARE"),
                         "R-UPLOAD": ("recovery", "V-FIRMWARE"),
                         "R-LIFE": ("firmware", "V-POWER"),
                         "R-MEASUREMENT": ("firmware", "V-MEASUREMENT")}
    for requirement_id, row in software_trace.items():
        if ((row.get("design_ref"), row.get("verification_id")) != software_expected[requirement_id]
                or row.get("verification_id") not in verification):
            raise ValueError("unresolved software design or wrong verification allocation")
    open_items = text_list(design["open_items"], "open items")
    power = inputs["power"]
    if power["reference"] != "battery_input" or power["event_charge_basis"] != "incremental_above_idle":
        raise ValueError("incompatible power reference or event-charge convention")
    sample_s = number(design["sample_period_s"], "sample period", positive=True)
    upload_s = number(design["upload_period_s"], "upload period", positive=True)
    capacity_records, retry_delays = policy_values(inputs["firmware_policy"])
    if type(design["sample_period_s"]) is not int or type(design["upload_period_s"]) is not int:
        raise ValueError("firmware periods must be integer seconds")
    if capacity_records * sample_s < upload_s or sum(retry_delays) >= upload_s:
        raise ValueError("firmware queue or retry schedule cannot cover a normal upload window")
    hours = number(requirements["R-LIFE"]["target_hours"], "target hours", positive=True)
    capacity = number(inputs["capacity"]["available_mAh"], "capacity", positive=True)
    common = number(inputs["bom_base"]["cny"], "common BOM")
    bom_limit = number(requirements["R-BOM"]["max_cny"], "BOM limit", positive=True)
    idle = number(power["idle_current_uA"], "idle current")
    sample_charge = number(power["sample_extra_charge_uAh"], "sampling charge")
    timing_ok = (
        sample_s <= number(requirements["R-SAMPLE"]["max_period_s"], "sample maximum", positive=True)
        and upload_s <= number(requirements["R-UPLOAD"]["max_period_s"], "upload maximum", positive=True)
    )
    if design["selected_radio"] not in radios:
        raise ValueError("unknown selected radio")
    alternatives = []
    for radio in radios.values():
        charge = number(radio["tx_extra_charge_uAh"], "transmission charge")
        current = idle + sample_charge * Decimal(3600) / sample_s + charge * Decimal(3600) / upload_s
        required = current * hours / Decimal(1000)
        cost = common + number(radio["bom_delta_cny"], "radio BOM")
        alternatives.append({
            "radio": radio["id"],
            "average_current_uA": str(current.normalize()),
            "required_capacity_mAh": str(required.normalize()),
            "capacity_margin_mAh": str((capacity - required).normalize()),
            "bom_cny": str(cost.normalize()),
            "power_budget_pass": required <= capacity,
            "bom_budget_pass": cost <= bom_limit,
        })
    selected = next(row for row in alternatives if row["radio"] == design["selected_radio"])
    passed = timing_ok and selected["power_budget_pass"] and selected["bom_budget_pass"]
    return {
        "case_id": inputs["case_id"], "input_snapshot": inputs["snapshot"],
        "design_id": design["design_id"], "selected_radio": design["selected_radio"],
        "data_kind": "synthetic_teaching", "requirements_traced": len(trace),
        "software_requirements_traced": len(software_trace),
        "timing_configuration_pass": timing_ok, "alternatives": alternatives,
        "checks_passed": passed,
        "status": "draft_ready_for_review" if passed else "draft_needs_revision",
        "firmware_target_verified": False, "physical_verified": False, "production_release_allowed": False,
        "open_items": open_items,
        "limits": "Only synthetic average-charge/BOM budgets and reference coverage were checked; no circuit, battery, RF or physical test was performed.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parent
    parser.add_argument("--inputs", type=Path, default=root / "inputs.json")
    parser.add_argument("--design", type=Path, default=root / "design.json")
    args = parser.parse_args()
    try:
        result = evaluate(json.loads(args.inputs.read_text(encoding="utf-8")), json.loads(args.design.read_text(encoding="utf-8")))
    except (ValueError, KeyError, TypeError, OSError, DecimalException) as error:
        print(json.dumps({"status": "invalid_input", "error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
