module struct_mod_10
  use iso_c_binding
  implicit none
  type, bind(c) :: my_struct_10
    integer(c_int) :: x
  end type
contains
  subroutine sub_10(s) bind(c)
    type(my_struct_10), value :: s
  end subroutine
end module