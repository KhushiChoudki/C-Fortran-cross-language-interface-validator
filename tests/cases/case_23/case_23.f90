module test_mod_23
  use iso_c_binding
  implicit none
contains
  subroutine sub_23(c) bind(c)
    character(kind=c_char) :: c
  end subroutine
end module