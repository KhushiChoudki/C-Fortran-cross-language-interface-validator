module test_mod_16
  use iso_c_binding
  implicit none
contains
  subroutine sub_16(ptr) bind(c)
    real(c_double), value :: ptr
  end subroutine
end module