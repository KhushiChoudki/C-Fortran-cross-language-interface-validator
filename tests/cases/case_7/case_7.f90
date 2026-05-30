module test_mod_7
  use iso_c_binding
  implicit none
contains
  subroutine sub_7(x) bind(c)
    real(c_double), value :: x
  end subroutine
end module