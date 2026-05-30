module test_mod_6
  use iso_c_binding
  implicit none
contains
  subroutine sub_6(x) bind(c)
    logical(4), value :: x
  end subroutine
end module