import subprocess
import re

class FlangParser:
    def __init__(self, flang_path="flang-new"):
        self.flang_path = flang_path

    def parse_fortran(self, fortran_file, include_paths=None):
        # Using -fdebug-dump-symbols to get detailed info about BIND(C) interfaces
        cmd = [
            self.flang_path,
            "-fc1",
        ]
        if include_paths:
            for p in include_paths:
                cmd.extend(["-I", p])
        
        cmd.extend([
            "-fdebug-dump-symbols",
            fortran_file
        ])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return self._parse_symbols(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error running flang: {e.stderr}")
            return None
        except Exception as e:
            print(f"Error parsing flang output: {e}")
            return None

    def _parse_symbols(self, dump_text):
        interfaces = {}
        structs = {}
        
        current_sub = None
        current_type = None
        
        lines = dump_text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Subprogram scope
            sub_scope_match = re.search(r'Subprogram scope:\s*([a-zA-Z0-9_]+)', line, re.IGNORECASE)
            if sub_scope_match:
                current_sub = {"name": sub_scope_match.group(1), "params_meta": {}, "params_order": [], "loc": {"line": i+1}}
                i += 1
                continue

            # BIND(C) summary line (can be multi-line)
            if current_sub and "BIND(C)" in line:
                full_line = line
                while "(" in full_line and ")" not in full_line and i + 1 < len(lines):
                    i += 1
                    full_line += " " + lines[i].strip()
                
                if "(" in full_line and ")" in full_line:
                    bind_name_match = re.search(r'bindName:([a-zA-Z0-9_]+)', full_line)
                    if bind_name_match:
                        bind_name = bind_name_match.group(1)
                        current_sub["bind_name"] = bind_name
                        
                        # Find the start parenthesis that follows the bindName
                        bind_name_pos = full_line.find(f"bindName:{bind_name}")
                        start_paren = full_line.find("(", bind_name_pos)
                        end_paren = full_line.rfind(")")
                        
                        if start_paren != -1 and end_paren != -1 and start_paren < end_paren:
                            arg_list_str = full_line[start_paren+1:end_paren]
                            # Split by comma, but be careful of commas inside parentheses (e.g. CHARACTER(1,1))
                            # For simplicity, we'll just handle the top-level commas
                            arg_list = []
                            bracket_level = 0
                            current_arg = ""
                            for char in arg_list_str:
                                if char == "(": bracket_level += 1
                                elif char == ")": bracket_level -= 1
                                elif char == "," and bracket_level == 0:
                                    arg_list.append(current_arg.strip())
                                    current_arg = ""
                                    continue
                                current_arg += char
                            if current_arg:
                                arg_list.append(current_arg.strip())
                            
                            for arg_item in arg_list:
                                arg_parts = arg_item.split(" ")
                                if arg_parts:
                                    arg_name = arg_parts[-1]
                                    current_sub["params_order"].append(arg_name)
                        
                        interfaces[bind_name] = current_sub

            # Dummy arguments metadata
            if current_sub:
                arg_match = re.search(r'^\s+([a-zA-Z0-9_]+).*dummy type: (.*)', line, re.IGNORECASE)
                if arg_match:
                    arg_name = arg_match.group(1)
                    arg_type = arg_match.group(2)
                    current_sub["params_meta"][arg_name] = {
                        "name": arg_name,
                        "type": self._normalize_fortran_type(arg_type),
                        "pass_by": "value" if "VALUE" in line else "reference"
                    }

            # Derived Type scope
            type_scope_match = re.search(r'DerivedType scope:\s*([a-zA-Z0-9_]+)', line, re.IGNORECASE)
            if type_scope_match:
                current_type = {"name": type_scope_match.group(1), "fields": [], "loc": {"line": i+1}}
                structs[current_type["name"]] = current_type
                current_sub = None
                i += 1
                continue
            
            if current_type:
                field_match = re.search(r'^\s+([a-zA-Z0-9_]+).*type: (.*)', line, re.IGNORECASE)
                if field_match and line.startswith("      ") and not "dummy" in line:
                    current_type["fields"].append({
                        "name": field_match.group(1),
                        "type": self._normalize_fortran_type(field_match.group(2))
                    })
                elif line.strip() and not line.startswith(" "):
                    current_type = None
            
            i += 1

        # Finalize interfaces by mapping meta to order
        final_interfaces = {}
        for bind_name, info in interfaces.items():
            params = []
            for arg_name in info["params_order"]:
                if arg_name in info["params_meta"]:
                    params.append(info["params_meta"][arg_name])
                else:
                    # Fallback for hidden arguments or parsing errors
                    params.append({"name": arg_name, "type": "unknown", "pass_by": "reference"})
            
            final_interfaces[bind_name] = {
                "name": info["name"],
                "params": params,
                "loc": info["loc"]
            }

        return {"interfaces": final_interfaces, "structs": structs}

    def _normalize_fortran_type(self, attrs):
        # Extract type info like Integer(4), Real(8), etc.
        type_match = re.search(r'(Integer|Real|Logical|Character|Type|Complex)(?:\((\d+)\))?', attrs, re.IGNORECASE)
        if type_match:
            base = type_match.group(1).lower()
            kind = type_match.group(2)
            if kind:
                return f"{base}({kind})"
            return base
        return "unknown"
