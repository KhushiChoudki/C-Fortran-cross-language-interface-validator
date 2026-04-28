import json
import subprocess
import os

class ClangParser:
    def __init__(self, clang_path="clang"):
        self.clang_path = clang_path

    def parse_header(self, header_file):
        cmd = [
            self.clang_path,
            "-Xclang", "-ast-dump=json",
            "-fsyntax-only",
            header_file
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            ast = json.loads(result.stdout)
            return self._extract_metadata(ast)
        except subprocess.CalledProcessError as e:
            print(f"Error running clang: {e.stderr}")
            return None
        except Exception as e:
            print(f"Error parsing clang output: {e}")
            return None

    def _extract_metadata(self, node):
        functions = {}
        structs = {}

        # The AST is a tree. We look for FunctionDecl and RecordDecl (structs).
        # This is a simplified traversal.
        
        stack = [(node, None)]
        while stack:
            curr, parent = stack.pop()
            
            kind = curr.get("kind")
            
            if kind == "FunctionDecl":
                name = curr.get("name")
                if name:
                    functions[name] = self._parse_function(curr)
            
            elif kind == "RecordDecl":
                name = curr.get("name")
                if name and curr.get("tagUsed") == "struct":
                    structs[name] = self._parse_struct(curr)
            
            elif kind == "TypedefDecl":
                # Check if this typedef refers to a struct
                type_name = curr.get("name")
                inner = curr.get("inner", [])
                if inner and inner[0].get("kind") == "ElaboratedType":
                    # Potentially a struct
                    structs[type_name] = self._parse_struct(curr)

            # Recurse into children
            for child in curr.get("inner", []):
                stack.append((child, curr))
        
        return {"functions": functions, "structs": structs}

    def _parse_function(self, node):
        params = []
        return_type = node.get("type", {}).get("qualType", "unknown")
        
        # Extract return type from the function type string
        # e.g., "int (int, double)" -> "int"
        if "(" in return_type:
            return_type = return_type.split("(")[0].strip()

        for child in node.get("inner", []):
            if child.get("kind") == "ParmVarDecl":
                params.append({
                    "name": child.get("name", ""),
                    "type": child.get("type", {}).get("qualType", "unknown"),
                    "loc": self._get_location(child)
                })
        
        return {
            "name": node.get("name"),
            "return_type": return_type,
            "params": params,
            "loc": self._get_location(node)
        }

    def _parse_struct(self, node):
        fields = []
        for child in node.get("inner", []):
            if child.get("kind") == "FieldDecl":
                fields.append({
                    "name": child.get("name", ""),
                    "type": child.get("type", {}).get("qualType", "unknown"),
                    "loc": self._get_location(child)
                })
        return {
            "name": node.get("name"),
            "fields": fields,
            "loc": self._get_location(node)
        }

    def _get_location(self, node):
        loc = node.get("loc", {})
        return {
            "file": loc.get("file", "unknown"),
            "line": loc.get("line", 0),
            "col": loc.get("col", 0)
        }
