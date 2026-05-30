module test_mod_18
  use iso_c_binding
  implicit none
contains
  subroutine sub_18(x) bind(c)
    integer(c_int), value :: x
  end subroutine
end module