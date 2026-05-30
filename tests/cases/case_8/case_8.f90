module test_mod_8
  use iso_c_binding
  implicit none
contains
  subroutine sub_8(x) bind(c)
    integer(c_int), value :: x
  end subroutine
end module