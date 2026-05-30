module test_mod_19
  use iso_c_binding
  implicit none
contains
  subroutine sub_19(cols, rows) bind(c)
    integer(c_int), value :: cols
    integer(c_int), value :: rows
  end subroutine
end module