module test_mod_27
  use iso_c_binding
  implicit none
contains
  subroutine sub_27(val) bind(c)
    real(c_double) :: val
  end subroutine
end module