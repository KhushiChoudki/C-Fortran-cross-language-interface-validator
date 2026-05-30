module struct_mod_22
  use iso_c_binding
  implicit none
  type, bind(c) :: val_struct_22
    real(c_double) :: val
  end type
contains
  subroutine sub_22(s) bind(c)
    type(val_struct_22), value :: s
  end subroutine
end module