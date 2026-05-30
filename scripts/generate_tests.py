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
        "subroutine sub(x) bind(c, name=\"wrong_name\")\n  integer(4) :: x\nend subroutine"
    )

    # 6. Bool vs Logical size mismatch
    create_test_case("case_6",
        "void sub_6(_Bool x);",
        "module test_mod_6\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_6(x) bind(c)\n    logical(4), value :: x\n  end subroutine\nend module"
    )

    # 7. Float vs Double mismatch
    create_test_case("case_7",
        "void sub_7(float x);",
        "module test_mod_7\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_7(x) bind(c)\n    real(c_double), value :: x\n  end subroutine\nend module"
    )

    # 8. Short vs Int mismatch
    create_test_case("case_8",
        "void sub_8(short x);",
        "module test_mod_8\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_8(x) bind(c)\n    integer(c_int), value :: x\n  end subroutine\nend module"
    )

    # 9. Long vs Int mismatch
    create_test_case("case_9",
        "void sub_9(long x);",
        "module test_mod_9\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_9(x) bind(c)\n    integer(c_int), value :: x\n  end subroutine\nend module"
    )

    # 10. Struct field count mismatch
    create_test_case("case_10",
        "struct my_struct_10 { int x; double y; };\nvoid sub_10(struct my_struct_10 s);",
        "module struct_mod_10\n  use iso_c_binding\n  implicit none\n  type, bind(c) :: my_struct_10\n    integer(c_int) :: x\n  end type\ncontains\n  subroutine sub_10(s) bind(c)\n    type(my_struct_10), value :: s\n  end subroutine\nend module"
    )

    # 11. Struct field type mismatch
    create_test_case("case_11",
        "struct my_struct_11 { int x; double y; };\nvoid sub_11(struct my_struct_11 s);",
        "module struct_mod_11\n  use iso_c_binding\n  implicit none\n  type, bind(c) :: my_struct_11\n    integer(c_int) :: x\n    integer(c_int) :: y\n  end type\ncontains\n  subroutine sub_11(s) bind(c)\n    type(my_struct_11), value :: s\n  end subroutine\nend module"
    )

    # 12. Struct field order mismatch
    create_test_case("case_12",
        "struct my_struct_12 { int x; double y; };\nvoid sub_12(struct my_struct_12 s);",
        "module struct_mod_12\n  use iso_c_binding\n  implicit none\n  type, bind(c) :: my_struct_12\n    real(c_double) :: y\n    integer(c_int) :: x\n  end type\ncontains\n  subroutine sub_12(s) bind(c)\n    type(my_struct_12), value :: s\n  end subroutine\nend module"
    )

    # 13. Const pointer mismatch
    create_test_case("case_13",
        "void sub_13(const int *x);",
        "module test_mod_13\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_13(x) bind(c)\n    integer(c_int), value :: x\n  end subroutine\nend module"
    )

    # 14. String vs Character pointer size/pass mismatch
    create_test_case("case_14",
        "void sub_14(char *s);",
        "module test_mod_14\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_14(s) bind(c)\n    character(kind=c_char), value :: s\n  end subroutine\nend module"
    )

    # 15. Void pointer to C mismatch
    create_test_case("case_15",
        "void sub_15(void *ptr);",
        "module test_mod_15\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_15(ptr) bind(c)\n    integer(c_int), value :: ptr\n  end subroutine\nend module"
    )

    # 16. Double pointer mismatch
    create_test_case("case_16",
        "void sub_16(double **ptr);",
        "module test_mod_16\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_16(ptr) bind(c)\n    real(c_double), value :: ptr\n  end subroutine\nend module"
    )

    # 17. Array parameter size mismatch
    create_test_case("case_17",
        "void sub_17(int arr[10]);",
        "module test_mod_17\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_17(arr) bind(c)\n    integer(c_int), value :: arr\n  end subroutine\nend module"
    )

    # 18. Function return value type mismatch
    create_test_case("case_18",
        "double sub_18(int x);",
        "module test_mod_18\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_18(x) bind(c)\n    integer(c_int), value :: x\n  end subroutine\nend module"
    )

    # 19. Swapped semantic parameter names
    create_test_case("case_19",
        "void sub_19(int rows, int cols);",
        "module test_mod_19\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_19(cols, rows) bind(c)\n    integer(c_int), value :: cols\n    integer(c_int), value :: rows\n  end subroutine\nend module"
    )

    # 20. Array no size parameter warning
    create_test_case("case_20",
        "void sub_20(double *data);",
        "module test_mod_20\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_20(data) bind(c)\n    real(c_double) :: data\n  end subroutine\nend module"
    )

    # 21. Complex number mismatch
    create_test_case("case_21",
        "void sub_21(float _Complex z);",
        "module test_mod_21\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_21(z) bind(c)\n    real(c_float), value :: z\n  end subroutine\nend module"
    )

    # 22. Typedef struct field type mismatch
    create_test_case("case_22",
        "struct val_struct_22 { int val; };\nvoid sub_22(struct val_struct_22 s);",
        "module struct_mod_22\n  use iso_c_binding\n  implicit none\n  type, bind(c) :: val_struct_22\n    real(c_double) :: val\n  end type\ncontains\n  subroutine sub_22(s) bind(c)\n    type(val_struct_22), value :: s\n  end subroutine\nend module"
    )

    # 23. Character value mismatch (missing value attribute)
    create_test_case("case_23",
        "void sub_23(char c);",
        "module test_mod_23\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_23(c) bind(c)\n    character(kind=c_char) :: c\n  end subroutine\nend module"
    )

    # 24. Short value to big integer kind
    create_test_case("case_24",
        "void sub_24(short val);",
        "module test_mod_24\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_24(val) bind(c)\n    integer(c_double), value :: val\n  end subroutine\nend module"
    )

    # 25. Long long value to small integer kind
    create_test_case("case_25",
        "void sub_25(long long val);",
        "module test_mod_25\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_25(val) bind(c)\n    integer(c_short), value :: val\n  end subroutine\nend module"
    )

    # 26. Float pointer mismatch
    create_test_case("case_26",
        "void sub_26(float *val);",
        "module test_mod_26\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_26(val) bind(c)\n    real(c_double), value :: val\n  end subroutine\nend module"
    )

    # 27. Double value mismatch (missing value attribute)
    create_test_case("case_27",
        "void sub_27(double val);",
        "module test_mod_27\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_27(val) bind(c)\n    real(c_double) :: val\n  end subroutine\nend module"
    )

    # 28. Array dimension mismatch
    create_test_case("case_28",
        "void sub_28(float matrix[3][5]);",
        "module test_mod_28\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_28(matrix) bind(c)\n    real(c_float), value :: matrix\n  end subroutine\nend module"
    )

    # 29. Size_t vs small integer type
    create_test_case("case_29",
        "void sub_29(size_t n);",
        "module test_mod_29\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_29(n) bind(c)\n    integer(c_short), value :: n\n  end subroutine\nend module"
    )

    # 30. Unsigned int mismatch
    create_test_case("case_30",
        "void sub_30(unsigned int x);",
        "module test_mod_30\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_30(x) bind(c)\n    integer(c_short), value :: x\n  end subroutine\nend module"
    )

    # 31. Nested struct field type mismatch
    create_test_case("case_31",
        "struct inner_s { int val; };\nstruct outer_s { struct inner_s inner; };\nvoid sub_31(struct outer_s s);",
        "module struct_mod_31\n  use iso_c_binding\n  implicit none\n  type, bind(c) :: inner_s\n    real(c_double) :: val\n  end type\n  type, bind(c) :: outer_s\n    type(inner_s) :: inner\n  end type\ncontains\n  subroutine sub_31(s) bind(c)\n    type(outer_s), value :: s\n  end subroutine\nend module"
    )

    print("[+] Generated 31 diverse test cases in tests/cases/")

if __name__ == "__main__":
    main()
