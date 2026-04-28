import re

FORTRAN_TYPE_MAP = {
    "integer(c_int)": "int",
    "real(c_float)": "float",
    "real(c_double)": "double",
    "logical(c_bool)": "bool",
    "character(kind=c_char)": "char",
    "type(c_ptr)": "void",
}

C_TYPE_ALIASES = {
    "int": "int",
    "float": "float",
    "double": "double",
    "char": "char",
    "void": "void",
    "_Bool": "bool",
    "bool": "bool",
}

def mk_param(name, type_kind, base_type, passing_mode, rank=0, pointer_depth=0, source=None, raw=None):
    """Creates a normalized parameter dictionary."""
    return {
        "name": name,
        "type_kind": type_kind,
        "base_type": base_type,
        "passing_mode": passing_mode,
        "rank": rank,
        "pointer_depth": pointer_depth,
        "source": source,
        "raw": raw,
    }

def mk_proc(name, symbol, kind, return_type, params, source=None, raw=None):
    """Creates a normalized procedure dictionary."""
    return {
        "name": name,
        "symbol": symbol,
        "kind": kind,
        "return_type": return_type,
        "params": params,
        "source": source,
        "raw": raw,
    }

def mk_record(name, fields, source=None, raw=None):
    """Creates a normalized record (struct) dictionary."""
    return {"name": name, "fields": fields, "source": source, "raw": raw}

def walk_ast(node):
    """Recursively walks a Clang AST node and yields all children."""
    yield node
    for child in node.get("inner", []) or []:
        yield from walk_ast(child)

def normalize_c_type(s):
    """Normalizes a C type string for easier parsing."""
    s = re.sub(r"\s+", " ", s.strip())
    s = s.replace("const ", "").replace("volatile ", "").strip()
    s = s.replace("struct ", "")
    return s

def parse_c_type(s):
    """Parses a normalized C type string into its components."""
    s = normalize_c_type(s)
    pointer_depth = s.count("*")
    base = s.replace("*", "").strip()
    base = C_TYPE_ALIASES.get(base, base)

    if base == "void" and pointer_depth > 0:
        return base, "opaque", "pointer", pointer_depth
    if pointer_depth > 0:
        return base, "pointer", "pointer", pointer_depth
    if base == "void":
        return base, "void", "value", 0
    return base, "scalar", "value", 0

def parse_fortran_type(type_spec):
    """Parses a Fortran type specification into its common type and kind."""
    key = re.sub(r"\s+", " ", type_spec.strip().lower())
    base = FORTRAN_TYPE_MAP.get(key, key)
    if base == "void":
        return base, "opaque"
    if key.startswith("type(") and "c_ptr" not in key:
        return key[5:-1].strip(), "record"
    return base, "scalar"
