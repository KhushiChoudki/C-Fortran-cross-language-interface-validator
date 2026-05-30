module test_mod_30
  use iso_c_binding
  implicit none
contains
  subroutine sub_30(x) bind(c)
    integer(c_short), value :: x
  end subroutine
end module