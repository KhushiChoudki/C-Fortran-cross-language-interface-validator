module test_mod_9
  use iso_c_binding
  implicit none
contains
  subroutine sub_9(x) bind(c)
    integer(c_int), value :: x
  end subroutine
end module