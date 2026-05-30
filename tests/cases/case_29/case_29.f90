module test_mod_29
  use iso_c_binding
  implicit none
contains
  subroutine sub_29(n) bind(c)
    integer(c_short), value :: n
  end subroutine
end module