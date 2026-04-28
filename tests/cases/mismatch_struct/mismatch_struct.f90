module struct_mod
  use iso_c_binding
  type, bind(c) :: my_struct
    integer(c_int) :: x
    integer(c_int) :: y ! Mismatch: C has double
  end type
contains
  subroutine sub(s) bind(c)
    type(my_struct), value :: s
  end subroutine
end module
