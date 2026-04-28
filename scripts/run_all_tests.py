import os
import subprocess

def main():
    cases_dir = "tests/cases"
    clang_bin = r"C:\Program Files\LLVM\bin\clang.exe"
    flang_bin = r"C:\Program Files\LLVM\bin\flang-new.exe"
    
    cases = os.listdir(cases_dir)
    total = 0
    passed = 0
    
    print(f"{'Test Case':<30} | {'Status':<10} | {'Issues Found'}")
    print("-" * 60)
    
    for case in cases:
        total += 1
        f90 = os.path.join(cases_dir, case, f"{case}.f90")
        h = os.path.join(cases_dir, case, f"{case}.h")
        
        if not os.path.exists(f90) or not os.path.exists(h):
            continue
            
        cmd = [
            "python", "fc_validator.py",
            "--fortran", f90,
            "--c", h,
            "--clang", clang_bin,
            "--flang", flang_bin
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        issues = []
        for line in result.stdout.splitlines():
            if line.strip().startswith("- ["):
                issues.append(line.strip())
        
        status = "DETECTED" if issues else "CLEAN"
        print(f"{case:<30} | {status:<10} | {len(issues)} issues")
        
    print(f"\n[+] Processed {total} test cases.")

if __name__ == "__main__":
    main()
