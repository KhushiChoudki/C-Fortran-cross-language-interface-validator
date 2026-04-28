import argparse
import sys
import os
from parsers.clang_parser import ClangParser
from parsers.flang_parser import FlangParser
from engine.comparator import Comparator

def main():
    parser = argparse.ArgumentParser(description="Fortran-C Cross-Language Interface Validator")
    parser.add_argument("--fortran", required=True, help="Path to Fortran source file")
    parser.add_argument("--c", required=True, help="Path to C header file")
    parser.add_argument("--clang", default="clang", help="Path to clang executable")
    parser.add_argument("--flang", default="flang-new", help="Path to flang-new executable")
    
    args = parser.parse_args()

    print(f"[*] Analyzing C header: {args.c}")
    c_parser = ClangParser(args.clang)
    c_metadata = c_parser.parse_header(args.c)
    if not c_metadata:
        print("[!] Failed to parse C header.")
        sys.exit(1)

    print(f"[*] Analyzing Fortran source: {args.fortran}")
    f_parser = FlangParser(args.flang)
    
    # Try to auto-detect flang include path
    flang_inc = os.path.join(os.path.dirname(os.path.dirname(args.flang)), "include", "flang")
    inc_paths = [flang_inc] if os.path.exists(flang_inc) else []
    
    f_metadata = f_parser.parse_fortran(args.fortran, include_paths=inc_paths)
    if not f_metadata:
        print("[!] Failed to parse Fortran source.")
        sys.exit(1)

    print("[*] Validating interfaces...")
    comparator = Comparator()
    results = comparator.validate(c_metadata, f_metadata)

    if not results:
        print("[+] SUCCESS: No compatibility issues found!")
    else:
        print(f"[!] Found {len(results)} issues:")
        for issue in results:
            print(f"  - [{issue['level']}] {issue['msg']} (Location: {issue['loc']})")

if __name__ == "__main__":
    main()
