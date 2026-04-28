import json
import subprocess
from pathlib import Path
from fc_validator.utils import mk_param, mk_proc, mk_record, walk_ast, parse_c_type

def run_command(cmd, check=True):
    """Helper to run shell commands and capture output."""
    # print(f"$ {cmd}") # Uncomment for debugging
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if p.returncode != 0:
        print(f"Error running command: {cmd}")
        print("STDOUT:", p.stdout)
        print("STDERR:", p.stderr)
        if check:
            raise RuntimeError(f"Command failed: {cmd}")
    return p

def extract_c_ast(c_header_path, output_json_path):
    """Extracts the Clang AST for a C header and saves it as JSON."""
    cmd = f"""
clang -x c -std=c11 -fsyntax-only \
  -Xclang -ast-dump=json \
  {c_header_path} > {output_json_path}
"""
    run_command(cmd, check=True)
    if not Path(output_json_path).exists():
        raise FileNotFoundError(f"C AST JSON not generated at {output_json_path}")
    print(f"C AST saved to: {output_json_path}")

def parse_c_ast_to_model(ast_json_path):
    """Parses the Clang AST JSON into the shared ABI model."""
    ast = json.loads(Path(ast_json_path).read_text())
    procedures = []
    records = []

    for node in walk_ast(ast):
        if node.get("kind") == "FunctionDecl":
            name = node.get("name")
            if not name:
                continue

            qtype = node.get("type", {}).get("qualType", "")
            m = re.match(r"^(.*)\(.*\)$", qtype) # Simplified regex assuming params are in parenthesis
            ret_raw = m.group(1).strip() if m else "void" # Default to void if parsing fails
            ret_base, ret_kind, ret_mode, ret_pd = parse_c_type(ret_raw)

            params = []
            for child in node.get("inner", []) or []:
                if child.get("kind") == "ParmVarDecl":
                    raw = child.get("type", {}).get("qualType", "")
                    base, kind, mode, pd = parse_c_type(raw)
                    params.append(mk_param(
                        name=child.get("name", ""),
                        type_kind=kind,
                        base_type=base,
                        passing_mode=mode,
                        rank=1 if pd > 0 else 0, # Simple heuristic for C arrays being pointers
                        pointer_depth=pd,
                        source=child.get("loc"),
                        raw=raw
                    ))

            procedures.append(mk_proc(
                name=name,
                symbol=name, # C symbol is usually just the name
                kind="subroutine" if ret_base == "void" and ret_pd == 0 else "function",
                return_type={
                    "base_type": ret_base,
                    "type_kind": ret_kind,
                    "passing_mode": ret_mode,
                    "pointer_depth": ret_pd,
                    "raw": ret_raw
                },
                params=params,
                source=node.get("loc"),
                raw=qtype
            ))

        if node.get("kind") == "RecordDecl" and node.get("tagUsed") == "struct" and node.get("completeDefinition"):
            name = node.get("name")
            if not name:
                continue
            fields = []
            for child in node.get("inner", []) or []:
                if child.get("kind") == "FieldDecl":
                    raw = child.get("type", {}).get("qualType", "")
                    base, kind, mode, pd = parse_c_type(raw)
                    fields.append(mk_param(
                        name=child.get("name", ""),
                        type_kind=kind,
                        base_type=base,
                        passing_mode=mode,
                        pointer_depth=pd, # Pointer depth for fields
                        source=child.get("loc"),
                        raw=raw
                    ))
            records.append(mk_record(name, fields, source=node.get("loc"), raw="struct"))

    return {"procedures": procedures, "records": records}

def get_c_model(c_header_path, build_dir):
    """Orchestrates C AST extraction and model parsing."""
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    c_ast_json_path = build_dir / "c_ast.json"
    extract_c_ast(c_header_path, c_ast_json_path)
    return parse_c_ast_to_model(c_ast_json_path)
