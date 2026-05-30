from engine.semantic_checker import SemanticChecker

class Comparator:
    # Mapping C types → expected Fortran numeric types (after normalization)
    C_TO_FORTRAN_TYPES = {
        # Integers
        "int":                "integer(4)",
        "unsigned int":       "integer(4)",
        "long":               "integer(8)",
        "unsigned long":      "integer(8)",
        "long long":          "integer(8)",
        "unsigned long long": "integer(8)",
        "short":              "integer(2)",
        "unsigned short":     "integer(2)",
        "size_t":             "integer(8)",
        "ptrdiff_t":          "integer(8)",
        "int8_t":             "integer(1)",
        "uint8_t":            "integer(1)",
        "int16_t":            "integer(2)",
        "uint16_t":           "integer(2)",
        "int32_t":            "integer(4)",
        "uint32_t":           "integer(4)",
        "int64_t":            "integer(8)",
        "uint64_t":           "integer(8)",
        # Characters / bool
        "char":               "character(1)",
        "unsigned char":      "character(1)",
        "_Bool":              "logical(1)",
        # Reals
        "float":              "real(4)",
        "double":             "real(8)",
        "long double":        "real(16)",
        # Complex
        "float _Complex":     "complex(4)",
        "double _Complex":    "complex(8)",
        "_Complex float":     "complex(4)",
        "_Complex double":    "complex(8)",
        # Pointers — C void* should map to type(c_ptr) i.e. integer(8)
        "void *":             "integer(8)",
    }

    # ISO_C_BINDING kind constants → numeric byte size
    ISO_C_KIND_MAP = {
        "c_int":            4,
        "c_short":          2,
        "c_long":           8,
        "c_long_long":      8,
        "c_signed_char":    1,
        "c_size_t":         8,
        "c_ptrdiff_t":      8,
        "c_int8_t":         1,
        "c_int16_t":        2,
        "c_int32_t":        4,
        "c_int64_t":        8,
        "c_float":          4,
        "c_double":         8,
        "c_long_double":    16,
        "c_float_complex":  4,
        "c_double_complex":  8,
        "c_bool":           1,
        "c_char":           1,
    }

    # numeric kind → base type (for comparison normalization)
    KIND_TO_BASE = {
        1: {"integer": "integer(1)", "logical": "logical(1)", "character": "character(1)", "real": "real(1)"},
        2: {"integer": "integer(2)", "logical": "logical(2)", "real": "real(2)"},
        4: {"integer": "integer(4)", "logical": "logical(4)", "real": "real(4)", "complex": "complex(4)"},
        8: {"integer": "integer(8)", "logical": "logical(8)", "real": "real(8)", "complex": "complex(8)"},
        16: {"integer": "integer(16)", "real": "real(16)", "complex": "complex(16)"},
    }

    def __init__(self):
        self.report = []

    def validate(self, c_metadata, f_metadata):
        self.report = []
        c_funcs = c_metadata["functions"]
        f_interfaces = f_metadata["interfaces"]

        for bind_name, f_info in f_interfaces.items():
            if bind_name not in c_funcs:
                if bind_name in c_metadata["structs"]:
                    self._compare_structs(bind_name, c_metadata["structs"][bind_name], f_info)
                    continue
                self.report.append({
                    "level": "ERROR",
                    "msg": f"Fortran BIND(C) interface '{bind_name}' has no matching C declaration.",
                    "loc": f"Fortran line {f_info['loc'].get('line', '?')}"
                })
                continue

            c_info = c_funcs[bind_name]
            self._compare_functions(bind_name, c_info, f_info)

        for type_name, f_info in f_metadata["structs"].items():
            if type_name in c_metadata["structs"]:
                self._compare_structs(type_name, c_metadata["structs"][type_name], f_info)

        return self.report

    # ─── Function comparison ────────────────────────────────────────────────
    def _compare_functions(self, name, c_info, f_info):
        c_ret = c_info.get("return_type", "void").replace("const ", "").strip()
        f_ret = f_info.get("return_type", "void")

        if c_ret == "void" and f_ret != "void":
            self.report.append({
                "level": "ERROR",
                "msg": f"Return type mismatch for '{name}': C is void (subroutine) but Fortran returns '{f_ret}'.",
                "loc": f"Fortran line {f_info['loc']['line']}"
            })
        elif c_ret != "void" and f_ret == "void":
            self.report.append({
                "level": "ERROR",
                "msg": f"Return type mismatch for '{name}': C returns '{c_ret}' but Fortran is a subroutine (void return).",
                "loc": f"Fortran line {f_info['loc']['line']}"
            })
        elif c_ret != "void":
            expected_f_ret = self._map_c_to_f(c_ret)
            if expected_f_ret and not self._types_compatible(expected_f_ret, f_ret):
                self.report.append({
                    "level": "ERROR",
                    "msg": f"Return type mismatch for '{name}': C returns '{c_ret}' (→ '{expected_f_ret}'), but Fortran returns '{f_ret}'.",
                    "loc": f"Fortran line {f_info['loc']['line']}"
                })

        # Parameter count
        if len(c_info["params"]) != len(f_info["params"]):
            self.report.append({
                "level": "ERROR",
                "msg": f"Parameter count mismatch for '{name}': C has {len(c_info['params'])}, Fortran has {len(f_info['params'])}.",
                "loc": f"Fortran line {f_info['loc']['line']}"
            })
            return

        for i, (c_param, f_param) in enumerate(zip(c_info["params"], f_info["params"])):
            self._compare_params(name, i, c_param, f_param, f_info["loc"]["line"])

        semantic_warnings = SemanticChecker.check_functions(name, c_info, f_info)
        self.report.extend(semantic_warnings)

    # ─── Parameter comparison ───────────────────────────────────────────────
    def _compare_params(self, func_name, idx, c_param, f_param, f_line):
        raw_c_type = c_param["type"].replace("const ", "").strip()
        f_type = f_param["type"]

        is_c_pointer = "*" in raw_c_type or ("[" in raw_c_type and "]" in raw_c_type)
        is_f_value   = f_param["pass_by"] == "value"

        # Pass-by-mode mismatch
        if is_c_pointer and is_f_value:
            self.report.append({
                "level": "ERROR",
                "msg": f"Pass-by mismatch in '{func_name}' arg {idx+1} ('{f_param['name']}'): "
                       f"C passes a pointer but Fortran has VALUE (scalar).",
                "loc": f"Fortran line {f_line}"
            })
        elif not is_c_pointer and not is_f_value:
            self.report.append({
                "level": "ERROR",
                "msg": f"Pass-by mismatch in '{func_name}' arg {idx+1} ('{f_param['name']}'): "
                       f"C passes by value but Fortran is missing VALUE attribute (reference semantics).",
                "loc": f"Fortran line {f_line}"
            })

        # Type mismatch — strip pointer decoration for type check
        c_base_type = raw_c_type.replace("*", "").replace("[", "").replace("]", "").strip()
        # also strip array dimension numbers e.g. "int 10" → "int"
        c_base_type = " ".join(w for w in c_base_type.split() if not w.isdigit())

        expected_f_type = self._map_c_to_f(c_base_type)
        if expected_f_type and not self._types_compatible(expected_f_type, f_type):
            self.report.append({
                "level": "WARNING",
                "msg": f"Type mismatch in '{func_name}' arg {idx+1} ('{f_param['name']}'): "
                       f"C type '{raw_c_type}' maps to '{expected_f_type}', but Fortran uses '{f_type}'.",
                "loc": f"Fortran line {f_line}"
            })

    # ─── Struct comparison ──────────────────────────────────────────────────
    def _compare_structs(self, name, c_struct, f_type):
        if len(c_struct["fields"]) != len(f_type["fields"]):
            self.report.append({
                "level": "ERROR",
                "msg": f"Struct field count mismatch for '{name}': "
                       f"C has {len(c_struct['fields'])} field(s), Fortran has {len(f_type['fields'])}.",
                "loc": f"Fortran line {f_type['loc']['line']}"
            })
            return

        for i, (c_field, f_field) in enumerate(zip(c_struct["fields"], f_type["fields"])):
            c_ftype = c_field["type"].strip()
            f_ftype = f_field["type"]
            expected_f_type = self._map_c_to_f(c_ftype)
            if expected_f_type and not self._types_compatible(expected_f_type, f_ftype):
                self.report.append({
                    "level": "ERROR",
                    "msg": f"Field type mismatch in struct '{name}' field '{c_field['name']}': "
                           f"C type '{c_ftype}' maps to '{expected_f_type}', but Fortran uses '{f_ftype}'.",
                    "loc": f"Fortran line {f_type['loc']['line']}"
                })

    # ─── Type helpers ────────────────────────────────────────────────────────
    def _map_c_to_f(self, c_type):
        """Map a C type string to the expected normalized Fortran type string."""
        clean = c_type.replace("const ", "").strip()
        if clean.startswith("struct "):
            struct_name = clean[7:].strip()
            return f"type({struct_name})"
        return self.C_TO_FORTRAN_TYPES.get(clean)

    def _resolve_iso_c_type(self, f_type_str):
        """
        Resolve an ISO_C_BINDING kind expression like 'integer(c_int)' → 'integer(4)'.
        Handles both numeric kinds (already normalized) and named c_ kinds.
        """
        import re
        m = re.match(r'(integer|real|logical|complex|character)\((\w+)\)', f_type_str.strip(), re.IGNORECASE)
        if not m:
            # bare type e.g. 'character'
            return f_type_str.lower()
        base = m.group(1).lower()
        kind_str = m.group(2).lower()

        if kind_str.isdigit():
            return f"{base}({kind_str})"

        # Named ISO_C kind
        numeric_bytes = self.ISO_C_KIND_MAP.get(kind_str)
        if numeric_bytes is not None:
            return f"{base}({numeric_bytes})"

        return f_type_str.lower()

    def _types_compatible(self, expected_f: str, actual_f: str) -> bool:
        """
        Compare two Fortran type strings for ABI compatibility,
        resolving ISO_C_BINDING kind names (c_int, c_double …) in actual_f.
        """
        expected_norm = self._resolve_iso_c_type(expected_f)
        actual_norm   = self._resolve_iso_c_type(actual_f)
        return expected_norm == actual_norm
