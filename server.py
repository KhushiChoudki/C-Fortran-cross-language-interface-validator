from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import time
from parsers.clang_parser import ClangParser
from parsers.flang_parser import FlangParser
from engine.comparator import Comparator
from engine.generator import FortranGenerator

app = Flask(__name__)
CORS(app)

CLANG_PATH = r"C:\Program Files\LLVM\bin\clang.exe" if os.name == 'nt' else "clang"
FLANG_PATH = r"C:\Program Files\LLVM\bin\flang-new.exe" if os.name == 'nt' else "flang-new"

@app.route('/api/validate', methods=['POST'])
def validate():
    data = request.json
    c_code = data.get('c_code', '')
    fortran_code = data.get('fortran_code', '')
    
    if not c_code or not fortran_code:
        return jsonify({"error": "Missing C or Fortran code"}), 400

    # Write code to temporary files
    with tempfile.NamedTemporaryFile(suffix='.h', delete=False, mode='w') as f_c:
        f_c.write(c_code)
        c_path = f_c.name
        
    with tempfile.NamedTemporaryFile(suffix='.f90', delete=False, mode='w') as f_f:
        f_f.write(fortran_code)
        f_path = f_f.name



    try:
        c_parser = ClangParser(CLANG_PATH)
        c_metadata = c_parser.parse_header(c_path)
        
        if not c_metadata:
            return jsonify({"error": "Failed to parse C code. Ensure valid syntax and clang is installed."}), 400
        if "syntax_error" in c_metadata:
            return jsonify({"results": [{"level": "ERROR", "msg": c_metadata["syntax_error"]["msg"], "loc": c_metadata["syntax_error"]["loc"]}]})

        f_parser = FlangParser(FLANG_PATH)
        f_metadata = f_parser.parse_fortran(f_path)
        
        if not f_metadata:
            return jsonify({"error": "Failed to parse Fortran code. Ensure valid syntax."}), 400
        if "syntax_error" in f_metadata:
            return jsonify({"results": [{"level": "ERROR", "msg": f_metadata["syntax_error"]["msg"], "loc": f_metadata["syntax_error"]["loc"]}]})

        comparator = Comparator()
        results = comparator.validate(c_metadata, f_metadata)
        
        return jsonify({"results": results})
    
    finally:
        # Cleanup temp files
        try:
            os.remove(c_path)
            os.remove(f_path)
        except:
            pass

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt.strip():
        return jsonify({"error": "No C code provided."}), 400

    # Write prompt to a temp header file
    with tempfile.NamedTemporaryFile(suffix='.h', delete=False, mode='w') as f_c:
        f_c.write(prompt)
        c_path = f_c.name

    try:
        c_parser = ClangParser(CLANG_PATH)
        c_metadata = c_parser.parse_header(c_path)
        
        if not c_metadata or (not c_metadata.get("functions") and not c_metadata.get("structs")):
            return jsonify({"generated": "! Error: Could not parse C code or no functions/structs found.\n! Please provide valid C headers."})

        generator = FortranGenerator()
        generated_code = generator.generate(c_metadata)
        
        return jsonify({"generated": generated_code})
    finally:
        try:
            os.remove(c_path)
        except:
            pass

TESTS_DIR = os.path.join(os.path.dirname(__file__), "tests", "cases")

@app.route('/api/testcases', methods=['GET'])
def get_testcases():
    cases = []
    if os.path.exists(TESTS_DIR):
        cases = [d for d in os.listdir(TESTS_DIR) if os.path.isdir(os.path.join(TESTS_DIR, d))]
        cases.sort()
    return jsonify({"cases": cases})

@app.route('/api/testcases/<case_name>', methods=['GET'])
def get_testcase(case_name):
    if case_name == 'run_all':
        return jsonify({"error": "Invalid endpoint"}), 400
        
    case_dir = os.path.join(TESTS_DIR, case_name)
    if not os.path.exists(case_dir):
        return jsonify({"error": "Test case not found"}), 404
        
    c_path = os.path.join(case_dir, f"{case_name}.h")
    f_path = os.path.join(case_dir, f"{case_name}.f90")
    
    c_code = ""
    f_code = ""
    if os.path.exists(c_path):
        with open(c_path, 'r', encoding='utf-8') as f: c_code = f.read()
    if os.path.exists(f_path):
        with open(f_path, 'r', encoding='utf-8') as f: f_code = f.read()
        
    return jsonify({"c_code": c_code, "fortran_code": f_code})

@app.route('/api/testcases/<case_name>', methods=['POST'])
def save_testcase(case_name):
    if case_name == 'run_all':
        return jsonify({"error": "Invalid endpoint"}), 400
        
    data = request.json
    c_code = data.get('c_code', '')
    f_code = data.get('fortran_code', '')
    
    case_dir = os.path.join(TESTS_DIR, case_name)
    os.makedirs(case_dir, exist_ok=True)
    
    with open(os.path.join(case_dir, f"{case_name}.h"), 'w', encoding='utf-8') as f:
        f.write(c_code)
    with open(os.path.join(case_dir, f"{case_name}.f90"), 'w', encoding='utf-8') as f:
        f.write(f_code)
        
    return jsonify({"success": True})

@app.route('/api/testcases/run_all', methods=['POST'])
def run_all_testcases():
    cases = []
    if os.path.exists(TESTS_DIR):
        cases = [d for d in os.listdir(TESTS_DIR) if os.path.isdir(os.path.join(TESTS_DIR, d))]
        cases.sort()
        
    results = {}
    for case in cases:
        c_path = os.path.join(TESTS_DIR, case, f"{case}.h")
        f_path = os.path.join(TESTS_DIR, case, f"{case}.f90")
        
        if not os.path.exists(c_path) or not os.path.exists(f_path):
            continue
            
        try:
            c_parser = ClangParser(CLANG_PATH)
            c_metadata = c_parser.parse_header(c_path)
            if not c_metadata or "syntax_error" in c_metadata:
                results[case] = {"status": "error", "issues": 1}
                continue
                
            f_parser = FlangParser(FLANG_PATH)
            f_metadata = f_parser.parse_fortran(f_path)
            if not f_metadata or "syntax_error" in f_metadata:
                results[case] = {"status": "error", "issues": 1}
                continue
                
            comparator = Comparator()
            res = comparator.validate(c_metadata, f_metadata)
            
            if res:
                results[case] = {"status": "rejected", "issues": len(res)}
            else:
                results[case] = {"status": "accepted", "issues": 0}
        except Exception as e:
            results[case] = {"status": "error", "issues": 1}
            
    return jsonify({"results": results})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
