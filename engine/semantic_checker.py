class SemanticChecker:
    @staticmethod
    def check_functions(func_name, c_info, f_info):
        warnings = []
        
        # Array Size Prediction (Rule 3)
        # Collect all parameter names to check if size-like names exist
        param_names = [p["name"].lower() for p in c_info["params"]]
        has_size_param = any(s in param_names for s in ["size", "len", "length", "n", "m", "k", "l", "rows", "cols", "dim"])

        for i, (c_param, f_param) in enumerate(zip(c_info["params"], f_info["params"])):
            c_name = c_param["name"]
            f_name = f_param["name"]
            c_type = c_param["type"]
            
            # Intent Checking (Rule 2)
            # If names exist and don't match (case-insensitive)
            if c_name and f_name and c_name.lower() != f_name.lower():
                warnings.append({
                    "level": "WARNING",
                    "msg": f"Semantic Intent: Parameter {i+1} is named '{f_name}' in Fortran but maps to '{c_name}' in C. Did you swap arguments?",
                    "loc": f"Fortran line {f_param.get('loc', {}).get('line', '?')}" # will map to editor
                })
            
            # Array Size Prediction
            is_c_pointer = "*" in c_type or "[" in c_type
            
            array_like_names = ["arr", "array", "vec", "vector", "matrix", "buf", "buffer", "data", "list", "str", "string"]
            is_array_like = any(a in c_name.lower() for a in array_like_names) or "[" in c_type
            
            if is_c_pointer and is_array_like and not has_size_param and "void" not in c_type:
                warnings.append({
                    "level": "WARNING",
                    "msg": f"Array Size Prediction: '{c_name}' appears to be an array/buffer, but no size parameter (e.g., 'n', 'size') was found.",
                    "loc": f"C: {c_param.get('loc', {}).get('file', '?')}:{c_param.get('loc', {}).get('line', '?')}"
                })

        return warnings
