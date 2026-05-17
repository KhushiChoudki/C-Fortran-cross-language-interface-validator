import requests
import json

c_code = 'void do_math(int rows, int cols, double *matrix);'
f_code = """module test_mod
    use iso_c_binding
    implicit none

    interface
        subroutine do_math(rows, cols, matrix) bind(C, name="do_math")
            import :: c_int, c_double

            integer(c_int), value :: rfwrows
            integer(c_int), value :: cols
            real(c_double)        :: matrix(*)

        end subroutine do_math
    end interface
end module test_mod"""

res = requests.post('http://127.0.0.1:5000/api/validate', json={'c_code': c_code, 'fortran_code': f_code})
print(res.status_code)
print(json.dumps(res.json(), indent=2))
