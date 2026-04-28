import os

def create_test_case(name, c_content, f_content):
    test_dir = f"tests/cases/{name}"
    os.makedirs(test_dir, exist_ok=True)
    with open(f"{test_dir}/{name}.h", "w") as f:
        f.write(c_content)
    with open(f"{test_dir}/{name}.f90", "w") as f:
        f.write(f_content)

def main():
    os.makedirs("tests/cases", exist_ok=True)

    # 1. Scalar type mismatch
    create_test_case("mismatch_scalar", 
        "void sub(int x);", 
        "subroutine sub(x) bind(c)\n  real(8) :: x\nend subroutine"
    )

    # 2. Argument count mismatch
    create_test_case("mismatch_count",
        "void sub(int x, int y);",
        "subroutine sub(x) bind(c)\n  integer(4) :: x\nend subroutine"
    )

    # 3. Pass-by-value vs Reference (C value, F reference)
    create_test_case("mismatch_passby_1",
        "void sub(int x);",
        "subroutine sub(x) bind(c)\n  integer(4) :: x\nend subroutine"
    )

    # 4. Pass-by-value vs Reference (C pointer, F value)
    create_test_case("mismatch_passby_2",
        "void sub(int *x);",
        "subroutine sub(x) bind(c)\n  integer(4), value :: x\nend subroutine"
    )

    # 5. Name mismatch (BIND(C) name)
    create_test_case("mismatch_name",
        "void sub_c(int x);",
        "subroutine sub(x) bind(c, name='wrong_name')\n  integer(4) :: x\nend subroutine"
    )

    # ... generate more ...
    for i in range(6, 31):
        create_test_case(f"case_{i}", 
            f"void sub_{i}(double x);", 
            f"subroutine sub_{i}(x) bind(c)\n  integer(4) :: x\nend subroutine"
        )

    print("[+] Generated 30 test cases in tests/cases/")

if __name__ == "__main__":
    main()
