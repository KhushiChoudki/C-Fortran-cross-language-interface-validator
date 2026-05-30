module test_mod_20
  use iso_c_binding
  implicit none
contains
  subroutine sub_20(data) bind(c)
    real(c_double) :: data
  end subroutine
end module