module test_mod_14
  use iso_c_binding
  implicit none
contains
  subroutine sub_14(s) bind(c)
    character(kind=c_char), value :: s
  end subroutine
end module