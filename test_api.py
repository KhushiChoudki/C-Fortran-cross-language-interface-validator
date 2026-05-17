import requests
import json

c_code = '''
struct Vector3D {
    double x;
    double y;
    double z;
};
void update_velocity(struct Vector3D *vec, int dt, double scale);
'''
f_code = '''module physics_interfaces
use iso_c_binding
implicit none
type, bind(C) :: Vector3D
real(c_double) :: x
real(c_double) :: y
real(c_double) :: z
end type Vector3D
interface
subroutine update_velocity(vec, dt, scale) bind(C, name="update_velocity")
import :: c_int, c_double, Vector3D
type(Vector3D) :: vec
integer(c_int), value :: dt
real(c_double), value :: scale
end subroutine update_velocity
end interface
end module physics_interfaces'''

res = requests.post('http://127.0.0.1:5000/api/validate', json={'c_code': c_code, 'fortran_code': f_code})
print(res.status_code)
print(json.dumps(res.json(), indent=2))
