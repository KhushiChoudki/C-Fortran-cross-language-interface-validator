module struct_mod_31
  use iso_c_binding
  implicit none
  type, bind(c) :: inner_s
    real(c_double) :: val
  end type
  type, bind(c) :: outer_s
    type(inner_s) :: inner
  end type
contains
  subroutine sub_31(s) bind(c)
    type(outer_s), value :: s
  end subroutine
end module