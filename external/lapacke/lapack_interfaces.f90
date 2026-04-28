
module lapack_interfaces
  use iso_c_binding
  contains
subroutine LAPACKE_dgetrf( matrix_layout, m, n, a, lda, ipiv ) bind(c, name="LAPACKE_dgetrf")
  integer(c_int), value :: matrix_layout
  integer(c_int), value :: m
  integer(c_int), value :: n
  real(c_double) :: a(*)
  integer(c_int), value :: lda
  integer(c_int) :: ipiv(*)
end subroutine
end module
