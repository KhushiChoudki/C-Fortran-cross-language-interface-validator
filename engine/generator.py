class FortranGenerator:
    C_TO_F_KIND = {
        "int": "integer(c_int)",
        "long": "integer(c_long)",
        "long long": "integer(c_long_long)",
        "short": "integer(c_short)",
        "char": "character(kind=c_char)",
        "float": "real(c_float)",
        "double": "real(c_double)",
        "void *": "type(c_ptr)",
        "_Bool": "logical(c_bool)",
        "size_t": "integer(c_size_t)"
    }

    def generate(self, c_metadata):
        output = [
            "! Auto-generated Fortran BIND(C) Interfaces",
            "module generated_interfaces",
            "    use iso_c_binding",
            "    implicit none",
            ""
        ]

        # Generate Structs
        if c_metadata.get("structs"):
            for struct_name, struct_data in c_metadata["structs"].items():
                output.extend(self._generate_struct(struct_data))
                output.append("")

        # Generate Functions
        if c_metadata.get("functions"):
            output.append("    interface")
            for func_name, func_data in c_metadata["functions"].items():
                output.extend(self._generate_function(func_data))
                output.append("")
            output.append("    end interface")
            output.append("")

        output.append("end module generated_interfaces")
        return "\n".join(output)

    def _generate_struct(self, struct_data):
        lines = []
        name = struct_data["name"]
        lines.append(f"    type, bind(C) :: {name}")
        for field in struct_data["fields"]:
            f_type = self._map_type(field["type"])
            lines.append(f"        {f_type} :: {field['name']}")
        lines.append(f"    end type {name}")
        return lines

    def _generate_function(self, func_data):
        lines = []
        name = func_data["name"]
        ret_type = func_data["return_type"]
        is_function = ret_type != "void"
        
        args = [p["name"] if p["name"] else f"arg{i}" for i, p in enumerate(func_data["params"])]
        args_str = ", ".join(args)

        if is_function:
            lines.append(f"        function {name}({args_str}) bind(C, name=\"{name}\")")
        else:
            lines.append(f"        subroutine {name}({args_str}) bind(C, name=\"{name}\")")

        lines.append("            import :: " + ", ".join(list(set([k.split("(")[1].split(")")[0].replace("kind=", "") for k in self.C_TO_F_KIND.values() if "c_" in k]))))
        
        param_names = [p["name"].lower() for p in func_data["params"]]
        has_size_param = any(s in param_names for s in ["size", "len", "length", "n", "m", "k", "l", "rows", "cols", "dim"])

        for i, param in enumerate(func_data["params"]):
            p_name = param["name"] if param["name"] else f"arg{i}"
            c_type = param["type"].replace("const ", "").strip()
            
            is_pointer = "*" in c_type
            is_array = "[" in c_type
            f_type = self._map_type(c_type)
            
            if is_pointer or is_array:
                if "void" in c_type:
                    lines.append(f"            type(c_ptr), value :: {p_name}")
                elif is_array or has_size_param:
                    lines.append(f"            {f_type} :: {p_name}(*)")
                else:
                    lines.append(f"            {f_type} :: {p_name}")
            else:
                lines.append(f"            {f_type}, value :: {p_name}")

        if is_function:
            f_ret = self._map_type(ret_type)
            if "*" in ret_type:
                lines.append(f"            type(c_ptr) :: {name}")
            else:
                lines.append(f"            {f_ret} :: {name}")
            lines.append(f"        end function {name}")
        else:
            lines.append(f"        end subroutine {name}")

        return lines

    def _map_type(self, c_type):
        base_c = c_type.replace("*", "").replace("const", "").replace("[", "").replace("]", "").strip()
        return self.C_TO_F_KIND.get(base_c, "type(c_ptr) ! Unknown type")
