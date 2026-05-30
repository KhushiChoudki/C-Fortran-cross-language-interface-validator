module test_mod_17
  use iso_c_binding
  implicit none
contains
  subroutine sub_17(arr) bind(c)
    integer(c_int), value :: arr
  end subroutine
end module