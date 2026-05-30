module test_mod_15
  use iso_c_binding
  implicit none
contains
  subroutine sub_15(ptr) bind(c)
    integer(c_int), value :: ptr
  end subroutine
end module