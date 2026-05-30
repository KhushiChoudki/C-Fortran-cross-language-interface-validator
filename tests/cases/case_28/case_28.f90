module test_mod_28
  use iso_c_binding
  implicit none
contains
  subroutine sub_28(matrix) bind(c)
    real(c_float), value :: matrix
  end subroutine
end module