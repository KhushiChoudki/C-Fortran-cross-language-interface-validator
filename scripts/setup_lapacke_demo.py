import os

def main():
    os.makedirs("external/lapacke", exist_ok=True)
    
    # Minimal LAPACKE header for testing
    with open("external/lapacke/lapacke_minimal.h", "w") as f:
        f.write("""
#ifndef LAPACKE_MINIMAL_H
#define LAPACKE_MINIMAL_H

typedef int lapack_int;

lapack_int LAPACKE_dgetrf( int matrix_layout, lapack_int m, lapack_int n,
                           double* a, lapack_int lda, lapack_int* ipiv );

#endif
""")

    # The Fortran interface file
    with open("external/lapacke/lapack_interfaces.f90", "w") as f:
        f.write("""
subroutine LAPACKE_dgetrf( matrix_layout, m, n, a, lda, ipiv ) bind(c, name="LAPACKE_dgetrf")
  import :: c_int, c_double
  integer(c_int), value :: matrix_layout
  integer(c_int), value :: m
  integer(c_int), value :: n
  real(c_double) :: a(*)
  integer(c_int), value :: lda
  integer(c_int) :: ipiv(*)
end subroutine
""")

if __name__ == "__main__":
    main()
