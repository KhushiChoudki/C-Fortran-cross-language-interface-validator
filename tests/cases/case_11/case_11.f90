module struct_mod_11
  use iso_c_binding
  implicit none
  type, bind(c) :: my_struct_11
    integer(c_int) :: x
    integer(c_int) :: y
  end type
contains
  subroutine sub_11(s) bind(c)
    type(my_struct_11), value :: s
  end subroutine
end module