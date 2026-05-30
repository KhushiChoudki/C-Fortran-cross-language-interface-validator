module test_mod_26
  use iso_c_binding
  implicit none
contains
  subroutine sub_26(val) bind(c)
    real(c_double), value :: val
  end subroutine
end module