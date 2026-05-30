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
            return self._parse_symbols(result.stdout, fortran_file)
        except subprocess.CalledProcessError as e:
            err_text = e.stderr
            match = re.search(r':(\d+):\d+:\s+error:\s+(.*)', err_text)
            if match:
                return {"syntax_error": {"msg": f"Syntax Error: {match.group(2).strip()}", "loc": f"Fortran line {match.group(1)}"}}
            # Fallback if regex doesn't match
            first_line = err_text.splitlines()[0] if err_text else "Unknown syntax error"
            return {"syntax_error": {"msg": f"Syntax Error: {first_line}", "loc": "Fortran line 1"}}
        except Exception as e:
            print(f"Error parsing flang output: {e}")
            return None

    def _parse_symbols(self, dump_text, fortran_file=None):
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
                else:
                    # Check if this line declares the return type of the function (has same name as subroutine/function)
                    ret_match = re.search(r'^\s+([a-zA-Z0-9_]+).*type: (.*)', line, re.IGNORECASE)
                    if ret_match and ret_match.group(1).lower() == current_sub["name"].lower() and not "dummy" in line:
                        current_sub["return_type"] = self._normalize_fortran_type(ret_match.group(2))

            # Derived Type scope
            type_scope_match = re.search(r'DerivedType scope:\s*([a-zA-Z0-9_]+)', line, re.IGNORECASE)
            if type_scope_match:
                current_type = {"name": type_scope_match.group(1), "fields": [], "loc": {"line": i+1}}
                structs[current_type["name"]] = current_type
                current_sub = None
                i += 1
                continue
            
            if current_type:
                field_match = re.search(r'^\s+([a-zA-Z0-9_]+)(?:\s+size=\d+)?\s+offset=(\d+):.*type: (.*)', line, re.IGNORECASE)
                if field_match and line.startswith("      ") and not "dummy" in line:
                    current_type["fields"].append({
                        "name": field_match.group(1),
                        "offset": int(field_match.group(2)),
                        "type": self._normalize_fortran_type(field_match.group(3))
                    })
                elif line.strip() and not line.startswith(" "):
                    current_type = None
            
            i += 1

        # Sort struct fields by offset to preserve layout order
        for s_name, s_info in structs.items():
            s_info["fields"].sort(key=lambda f: f.get("offset", 0))

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
                "return_type": info.get("return_type", "void"),
                "loc": info["loc"]
            }

        # Try to scan the original Fortran file to locate correct declaration lines
        if fortran_file:
            try:
                with open(fortran_file, 'r', encoding='utf-8', errors='ignore') as f:
                    source_lines = f.read().splitlines()
                
                # Update subroutines/functions lines
                for bind_name, info in final_interfaces.items():
                    name = info["name"].lower()
                    for idx, src_line in enumerate(source_lines):
                        clean_line = src_line.strip().lower()
                        # Search for BIND(C) subroutine or function
                        if "subroutine" in clean_line and name in clean_line:
                            info["loc"]["line"] = idx + 1
                            break
                        if "function" in clean_line and name in clean_line:
                            info["loc"]["line"] = idx + 1
                            break

                # Update structs (derived types) lines
                for s_name, s_info in structs.items():
                    name = s_info["name"].lower()
                    for idx, src_line in enumerate(source_lines):
                        clean_line = src_line.strip().lower()
                        # Search for TYPE, BIND(C)
                        if "type" in clean_line and name in clean_line:
                            s_info["loc"]["line"] = idx + 1
                            break
            except Exception as ex:
                print(f"Error mapping original source lines: {ex}")

        return {"interfaces": final_interfaces, "structs": structs}

    def _normalize_fortran_type(self, attrs):
        """
        Normalize a Fortran type attribute string from flang's symbol dump.
        Handles both numeric kinds (Integer(4)) and ISO_C_BINDING named kinds (Integer(c_int)).
        Examples:
          'Integer(4)'           → 'integer(4)'
          'Real(8)'              → 'real(8)'
          'Integer(c_int)'       → 'integer(c_int)'
          'Logical(c_bool)'      → 'logical(c_bool)'
          'Character(1,KIND=1)'  → 'character(1)'
          'Type(my_struct_10)'   → 'type(my_struct_10)'
        """
        # Match base type + optional kind
        type_match = re.search(
            r'(Integer|Real|Logical|Character|Type|Complex)\(([^)]+)\)',
            attrs, re.IGNORECASE
        )
        if type_match:
            base = type_match.group(1).lower()
            raw_kind = type_match.group(2).strip()

            # CHARACTER may have shape like "1,KIND=1" — take the KIND part or first token
            if base == 'character':
                kind_part = raw_kind
                for part in raw_kind.split(','):
                    part = part.strip()
                    if part.upper().startswith('KIND='):
                        kind_part = part.split('=')[1].strip()
                        break
                    elif part.isdigit():
                        kind_part = part
                        break
                return f"character({kind_part})"

            # Numeric kind
            if raw_kind.isdigit():
                return f"{base}({raw_kind})"

            # Named ISO_C_BINDING kind (e.g. c_int, c_double) — preserve as-is in lowercase
            iso_kind = raw_kind.lower().split(',')[0].strip()
            return f"{base}({iso_kind})"

        # No parenthesised kind — bare type
        bare_match = re.search(r'(Integer|Real|Logical|Character|Complex)', attrs, re.IGNORECASE)
        if bare_match:
            return bare_match.group(1).lower()

        return "unknown"

