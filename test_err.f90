module physics_interfaces
use iso_c_binding
implicit none
type, bind(C) :: Vector3D
real(c_double) :: x
real(c_double) :: y
real(c_double) ::dwedfw z
end type Vector3D
end module physics_interfaces