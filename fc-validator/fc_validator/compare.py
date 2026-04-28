
def compare_scalar_types(fp, cp):
    """Compares scalar types between Fortran and C parameters."""
    if fp["base_type"] != cp["base_type"]:
        return False, f"scalar type mismatch: Fortran {fp['base_type']} vs C {cp['base_type']}"
    return True, None

def compare_type_compatibility(fp, cp):
    """Compares general type compatibility between Fortran and C parameters."""
    if fp["type_kind"] == "array":
        if cp["pointer_depth"] >= 1 and fp["base_type"] == cp["base_type"]:
            return True, None
        return False, f"array/pointer mismatch: Fortran {fp['base_type']} array vs C {cp['raw']}"

    if fp["type_kind"] == "opaque":
        if cp["base_type"] == "void" and cp["pointer_depth"] >= 1:
            return True, None
        return False, f"opaque pointer mismatch: Fortran type(c_ptr) vs C {cp['raw']}"

    if fp["type_kind"] == "record":
        if fp["base_type"] == cp["base_type"]:
            return True, None
        return False, f"record type mismatch: Fortran {fp['base_type']} vs C {cp['base_type']}"

    return compare_scalar_types(fp, cp)

def compare_passing_mode(fp, cp):
    """Compares passing mode compatibility between Fortran and C parameters."""
    if fp["passing_mode"] == "value":
        if cp["pointer_depth"] == 0:
            return True, None
        return False, f"passing-mode mismatch: Fortran VALUE vs C pointer {cp['raw']}"

    if fp["type_kind"] == "array":
        if cp["pointer_depth"] >= 1:
            return True, None
        return False, f"array passing mismatch: Fortran array vs C non-pointer {cp['raw']}"

    if fp["passing_mode"] == "reference":
        if cp["pointer_depth"] >= 1:
            return True, None
        return False, f"passing-mode mismatch: Fortran by-reference vs C by-value {cp['raw']}"

    return True, None

def compare_procedure(fortran_proc, c_proc):
    """Compares a Fortran procedure with a C procedure and returns a report."""
    summary = []
    per_param = []
    risk = 0
    has_error = False
    has_warning = False

    if fortran_proc["symbol"] != c_proc["symbol"]:
        summary.append({"level": "error", "issue": f"symbol mismatch: Fortran {fortran_proc['symbol']} vs C {c_proc['symbol']}"})
        has_error = True
        risk += 3

    if fortran_proc["kind"] == "subroutine" and c_proc["return_type"]["base_type"] != "void":
        summary.append({"level": "error", "issue": f"procedure kind mismatch: Fortran subroutine vs C {c_proc['return_type']['raw']}"})
        has_error = True
        risk += 3

    if fortran_proc["kind"] == "function" and c_proc["return_type"]["base_type"] == "void":
        summary.append({"level": "error", "issue": "procedure kind mismatch: Fortran function vs C void"})
        has_error = True
        risk += 3

    if len(fortran_proc["params"]) != len(c_proc["params"]):
        summary.append({"level": "error", "issue": f"parameter count mismatch: Fortran {len(fortran_proc['params'])} vs C {len(c_proc['params'])}"})
        has_error = True
        risk += 3

    # Compare parameters based on position
    for idx, (fpar, cpar) in enumerate(zip(fortran_proc["params"], c_proc["params"]), start=1):
        issues = []

        # Parameter name/order mismatch is a warning
        if fpar["name"].lower() != cpar["name"].lower():
            issues.append({
                "level": "warning",
                "issue": f"parameter name/order mismatch at position {idx}: Fortran '{fpar['name']}' vs C '{cpar['name']}'"
            })

        ok_type, msg = compare_type_compatibility(fpar, cpar)
        if not ok_type:
            issues.append({"level": "error", "issue": msg})

        ok_mode, msg = compare_passing_mode(fpar, cpar)
        if not ok_mode:
            issues.append({"level": "error", "issue": msg})

        if any(x["level"] == "error" for x in issues):
            has_error = True
            risk += 2
        elif any(x["level"] == "warning" for x in issues):
            has_warning = True
            risk += 1

        per_param.append({
            "index": idx,
            "fortran": fpar,
            "c": cpar,
            "issues": issues
        })
    
    # Handle cases where one has more parameters than the other (already added to summary)
    # Remaining parameters in Fortran but not C
    for idx in range(len(c_proc["params"]), len(fortran_proc["params"])):
        fpar = fortran_proc["params"][idx]
        per_param.append({
            "index": idx + 1,
            "fortran": fpar,
            "c": None,
            "issues": [{
                "level": "error",
                "issue": f"Fortran parameter '{fpar['name']}' at position {idx+1} has no matching C parameter"
            }]
        })
        has_error = True
        risk += 2
    # Remaining parameters in C but not Fortran
    for idx in range(len(fortran_proc["params"]), len(c_proc["params"])):
        cpar = c_proc["params"][idx]
        per_param.append({
            "index": idx + 1,
            "fortran": None,
            "c": cpar,
            "issues": [{
                "level": "error",
                "issue": f"C parameter '{cpar['name']}' at position {idx+1} has no matching Fortran parameter"
            }]
        })
        has_error = True
        risk += 2


    if has_error:
        status, severity = "incompatible", "error"
    elif has_warning:
        status, severity = "warning", "warning"
    else:
        status, severity = "compatible", "note"

    return {
        "symbol": fortran_proc["symbol"],
        "status": status,
        "severity": severity,
        "risk_score": risk,
        "summary": summary,
        "per_param": per_param
    }

def compare_record(fortran_record, c_record):
    """Compares a Fortran record with a C struct and returns a report."""
    summary = []
    per_field = []
    risk = 0
    has_error = False
    has_warning = False

    if len(fortran_record["fields"]) != len(c_record["fields"]):
        summary.append({"level": "error", "issue": f"field count mismatch: Fortran {len(fortran_record['fields'])} vs C {len(c_record['fields'])}"})
        has_error = True
        risk += 2

    for idx, (ff, cf) in enumerate(zip(fortran_record["fields"], c_record["fields"]), start=1):
        issues = []

        if ff["name"].lower() != cf["name"].lower():
            issues.append({"level": "warning", "issue": f"field name/order mismatch at position {idx}: Fortran '{ff['name']}' vs C '{cf['name']}'"})

        # For records, a direct base_type comparison is often sufficient for fields
        # More complex type comparisons might be needed for nested structs, but for simple scalars it's direct
        if ff["base_type"] != cf["base_type"]:
            issues.append({"level": "error", "issue": f"field type mismatch: Fortran {ff['base_type']} vs C {cf['base_type']}"})

        if any(x["level"] == "error" for x in issues):
            has_error = True
            risk += 2
        elif any(x["level"] == "warning" for x in issues):
            has_warning = True
            risk += 1

        per_field.append({
            "index": idx,
            "fortran": ff,
            "c": cf,
            "issues": issues
        })

    if has_error:
        status, severity = "incompatible", "error"
    elif has_warning:
        status, severity = "warning", "warning"
    else:
        status, severity = "compatible", "note"

    return {
        "record": fortran_record["name"],
        "status": status,
        "severity": severity,
        "risk_score": risk,
        "summary": summary,
        "per_field": per_field
    }

def validate_all(f_model, c_model):
    """Validates all Fortran procedures and records against C counterparts."""
    c_proc_map = {p["symbol"]: p for p in c_model["procedures"]}
    c_rec_map = {r["name"]: r for r in c_model["records"]}

    proc_reports = []
    for fp in f_model["procedures"]:
        cp = c_proc_map.get(fp["symbol"])
        if cp is None:
            proc_reports.append({
                "symbol": fp["symbol"],
                "status": "incompatible",
                "severity": "error",
                "risk_score": 3,
                "summary": [{"level": "error", "issue": "missing matching C symbol"}],
                "per_param": []
            })
        else:
            proc_reports.append(compare_procedure(fp, cp))

    rec_reports = []
    for fr in f_model["records"]:
        cr = c_rec_map.get(fr["name"])
        if cr is None:
            rec_reports.append({
                "record": fr["name"],
                "status": "warning",
                "severity": "warning",
                "risk_score": 1,
                "summary": [{"level": "warning", "issue": "missing matching C struct"}],
                "per_field": []
            })
        else:
            rec_reports.append(compare_record(fr, cr))

    return {"procedures": proc_reports, "records": rec_reports}
