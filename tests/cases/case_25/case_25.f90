module test_mod_25
  use iso_c_binding
  implicit none
contains
  subroutine sub_25(val) bind(c)
    integer(c_short), value :: val
  end subroutine
end module