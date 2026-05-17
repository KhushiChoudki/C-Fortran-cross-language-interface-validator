from engine.semantic_checker import SemanticChecker

class Comparator:
    # Mapping C types to Fortran ISO_C_BINDING kinds
    C_TO_FORTRAN_TYPES = {
        "int": "integer(4)",
        "long": "integer(8)",
        "long long": "integer(8)",
        "short": "integer(2)",
        "char": "character",
        "float": "real(4)",
        "double": "real(8)",
        "void *": "type(c_ptr)",
        "int *": "integer(4)", 
        "double *": "real(8)",
        "_Bool": "logical(1)",
    }

    def __init__(self):
        self.report = []

    def validate(self, c_metadata, f_metadata):
        c_funcs = c_metadata["functions"]
        f_interfaces = f_metadata["interfaces"]

        for bind_name, f_info in f_interfaces.items():
            if bind_name not in c_funcs:
                # Check if it's a struct/type instead
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

    def _compare_functions(self, name, c_info, f_info):
        # Compare parameter counts
        if len(c_info["params"]) != len(f_info["params"]):
            self.report.append({
                "level": "ERROR",
                "msg": f"Parameter count mismatch for '{name}': C has {len(c_info['params'])}, Fortran has {len(f_info['params'])}.",
                "loc": f"Fortran line {f_info['loc']['line']}"
            })
            return

        # Compare each parameter
        for i, (c_param, f_param) in enumerate(zip(c_info["params"], f_info["params"])):
            self._compare_params(name, i, c_param, f_param, f_info['loc']['line'])

        # Semantic Checks
        semantic_warnings = SemanticChecker.check_functions(name, c_info, f_info)
        self.report.extend(semantic_warnings)

    def _compare_params(self, func_name, idx, c_param, f_param, f_line):
        c_type = c_param["type"].replace("const ", "").strip()
        f_type = f_param["type"]
        
        # Check pass-by-value vs reference
        is_c_pointer = "*" in c_type or "[" in c_type
        is_f_value = f_param["pass_by"] == "value"

        if is_c_pointer and is_f_value:
            self.report.append({
                "level": "ERROR",
                "msg": f"Pass-by mismatch in '{func_name}' arg {idx+1} ({f_param['name']}): C is pointer but Fortran is VALUE.",
                "loc": f"Fortran line {f_line}"
            })
        elif not is_c_pointer and not is_f_value:
            # Note: Fortran passes by reference by default, which maps to C pointers
            # If C is NOT a pointer, and Fortran is NOT VALUE, then it's a mismatch
            self.report.append({
                "level": "ERROR",
                "msg": f"Pass-by mismatch in '{func_name}' arg {idx+1} ({f_param['name']}): C is value but Fortran is reference (missing VALUE attribute).",
                "loc": f"Fortran line {f_line}"
            })

        # Basic type compatibility check
        expected_f_type = self._map_c_to_f(c_type)
        if expected_f_type and expected_f_type != f_type:
             self.report.append({
                "level": "WARNING",
                "msg": f"Type mismatch in '{func_name}' arg {idx+1} ({f_param['name']}): C type '{c_type}' maps to '{expected_f_type}', but Fortran uses '{f_type}'.",
                "loc": f"Fortran line {f_line}"
            })

    def _compare_structs(self, name, c_struct, f_type):
        if len(c_struct["fields"]) != len(f_type["fields"]):
            self.report.append({
                "level": "ERROR",
                "msg": f"Struct field count mismatch for '{name}': C has {len(c_struct['fields'])}, Fortran has {len(f_type['fields'])}.",
                "loc": f"Fortran line {f_type['loc']['line']}"
            })
            return

        for i, (c_field, f_field) in enumerate(zip(c_struct["fields"], f_type["fields"])):
            c_ftype = c_field["type"].strip()
            f_ftype = f_field["type"]
            
            expected_f_type = self._map_c_to_f(c_ftype)
            if expected_f_type and expected_f_type != f_ftype:
                self.report.append({
                    "level": "ERROR",
                    "msg": f"Field type mismatch in struct '{name}' at field '{c_field['name']}': C type '{c_ftype}' maps to '{expected_f_type}', but Fortran uses '{f_ftype}'.",
                    "loc": f"Fortran line {f_type['loc']['line']}"
                })

    def _map_c_to_f(self, c_type):
        base_c = c_type.replace("*", "").strip()
        return self.C_TO_FORTRAN_TYPES.get(base_c)
