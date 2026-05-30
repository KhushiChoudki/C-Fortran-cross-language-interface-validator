module test_mod_21
  use iso_c_binding
  implicit none
contains
  subroutine sub_21(z) bind(c)
    real(c_float), value :: z
  end subroutine
end module