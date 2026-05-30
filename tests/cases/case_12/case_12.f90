module struct_mod_12
  use iso_c_binding
  implicit none
  type, bind(c) :: my_struct_12
    real(c_double) :: y
    integer(c_int) :: x
  end type
contains
  subroutine sub_12(s) bind(c)
    type(my_struct_12), value :: s
  end subroutine
end module