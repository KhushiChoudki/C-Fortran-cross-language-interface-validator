module test_mod_24
  use iso_c_binding
  implicit none
contains
  subroutine sub_24(val) bind(c)
    integer(c_double), value :: val
  end subroutine
end module