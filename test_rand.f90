module test_mod
    use iso_c_binding
    implicit none

    interface
        subroutine do_math(rows, cols, matrix) bind(C, name="do_math")
            import :: c_int, c_double

            derygerows
            integer(c_int), value :: cols
            real(c_double)        :: matrix(*)

        end subroutine do_math
    end interface
end module test_mod
