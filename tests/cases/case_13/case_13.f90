module test_mod_13
  use iso_c_binding
  implicit none
contains
  subroutine sub_13(x) bind(c)
    integer(c_int), value :: x
  end subroutine
end module