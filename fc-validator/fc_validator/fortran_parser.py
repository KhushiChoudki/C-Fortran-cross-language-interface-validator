import re
from pathlib import Path
from fc_validator.utils import mk_param, mk_proc, mk_record, parse_fortran_type

def extract_bind_name(line):
    """Extracts the C name from a BIND(C, NAME='...') clause."""
    m = re.search(r'bind\s*\(\s*c\s*(?:,\s*name\s*=\s*"([^"]+)")?\s*\)', line, re.I)
    return m.group(1) if m and m.group(1) else None

def parse_fortran_decl(line, lineno):
    """Parses a Fortran declaration line into a list of normalized parameters."""
    s = line.strip()
    if "::" not in s:
        return []

    left, right = s.split("::", 1)
    attrs = [a.strip() for a in left.split(",")]
    type_spec = attrs[0].strip()
    attr_flags = {a.strip().lower() for a in attrs[1:]}

    names = [x.strip() for x in right.split(",") if x.strip()]
    out = []

    for item in names:
        pname = item
        rank = 0
        type_kind_hint = None

        if "(" in item and ")" in item:
            pname = item[:item.index("(")].strip()
            shape = item[item.index("(")+1:item.rindex(")")].strip()
            if shape == "*" or shape != "": # Treat any non-empty shape as an array for now
                rank = 1
                type_kind_hint = "array"

        base_type, default_kind = parse_fortran_type(type_spec)

        if base_type == "void":
            type_kind = "opaque"
            passing_mode = "pointer"
        elif type_kind_hint == "array":
            type_kind = "array"
            passing_mode = "pointer"
        else:
            type_kind = default_kind
            passing_mode = "value" if "value" in attr_flags else "reference"

        out.append(mk_param(
            name=pname,
            type_kind=type_kind,
            base_type=base_type,
            passing_mode=passing_mode,
            rank=rank,
            pointer_depth=1 if passing_mode in ("pointer", "reference") and type_kind in ("array", "opaque") else 0, # Fortran arrays are passed by reference
            source={"line": lineno},
            raw=line.rstrip()
        ))
    return out

def extract_fortran_model(fortran_path):
    """Extracts Fortran BIND(C) procedures and records into the shared ABI model."""
    lines = Path(fortran_path).read_text().splitlines()
    procedures, records = [], []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Match subroutine or function declaration with BIND(C)
        m = re.match(r'^(subroutine|function)\s+(\w+)\s*\((.*?)\)\s*bind\s*\(.*\)', line, re.I)
        if m:
            kind = m.group(1).lower()
            name = m.group(2)
            args_str = m.group(3)
            args = [a.strip() for a in args_str.split(",") if a.strip()]
            symbol = extract_bind_name(line) or name # Use explicit name or Fortran name as symbol

            decls = []
            raw_block = [lines[i]]
            j = i + 1
            # Collect declarations within the interface block
            while j < len(lines):
                raw_block.append(lines[j])
                if re.match(rf'^\s*end\s+{kind}\b', lines[j], re.I): # End of subroutine/function
                    break
                decls.extend(parse_fortran_decl(lines[j], j + 1))
                j += 1

            decl_map = {d["name"].lower(): d for d in decls}
            ordered_params = []
            for a in args:
                # Fill in parameters based on order in signature and collected declarations
                ordered_params.append(decl_map.get(a.lower(), mk_param(
                    name=a,
                    type_kind="unknown", # Fallback for undeclared parameters
                    base_type="unknown",
                    passing_mode="reference", # Fortran default passing
                    source={"line": i + 1},
                    raw="missing declaration"
                )))

            procedures.append(mk_proc(
                name=name,
                symbol=symbol,
                kind=kind,
                return_type=None if kind == "subroutine" else { # Return type for functions
                    "base_type": "unknown", # Cannot easily determine from this parser without symbol table
                    "type_kind": "scalar",
                    "passing_mode": "value", # Fortran functions return by value (usually)
                    "pointer_depth": 0,
                    "raw": None
                },
                params=ordered_params,
                source={"line": i + 1},
                raw="\n".join(raw_block)
            ))
            i = j + 1 # Move past the end of the procedure block
            continue

        # Match TYPE, BIND(C) :: record_name
        m = re.match(r'^\s*type\s*,\s*bind\s*\(\s*c\s*\)\s*::\s*(\w+)', lines[i], re.I)
        if m:
            name = m.group(1)
            raw_block = [lines[i]]
            fields = []
            j = i + 1
            # Collect fields within the type block
            while j < len(lines):
                raw_block.append(lines[j])
                if re.match(r'^\s*end\s+type\b', lines[j], re.I): # End of type
                    break
                fields.extend(parse_fortran_decl(lines[j], j + 1))
                j += 1
            records.append(mk_record(name, fields, source={"line": i + 1}, raw="\n".join(raw_block)))
            i = j + 1 # Move past the end of the type block
            continue

        i += 1 # Move to the next line if no match

    return {"procedures": procedures, "records": records}
