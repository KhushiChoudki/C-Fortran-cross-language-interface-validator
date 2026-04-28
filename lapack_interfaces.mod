!mod$ v1 sum:6eb90d7b59c458fe
!need$ fc1ab5ddb0e0d965 n iso_c_binding
module lapack_interfaces
use iso_c_binding,only:c_associated
use iso_c_binding,only:c_funloc
use iso_c_binding,only:c_funptr
use iso_c_binding,only:c_f_pointer
use iso_c_binding,only:c_loc
use iso_c_binding,only:c_null_funptr
use iso_c_binding,only:c_null_ptr
use iso_c_binding,only:c_ptr
use iso_c_binding,only:c_sizeof
use iso_c_binding,only:operator(==)
use iso_c_binding,only:operator(/=)
use iso_c_binding,only:c_int8_t
use iso_c_binding,only:c_int16_t
use iso_c_binding,only:c_int32_t
use iso_c_binding,only:c_int64_t
use iso_c_binding,only:c_int128_t
use iso_c_binding,only:c_int
use iso_c_binding,only:c_short
use iso_c_binding,only:c_long
use iso_c_binding,only:c_long_long
use iso_c_binding,only:c_signed_char
use iso_c_binding,only:c_size_t
use iso_c_binding,only:c_intmax_t
use iso_c_binding,only:c_intptr_t
use iso_c_binding,only:c_ptrdiff_t
use iso_c_binding,only:c_int_least8_t
use iso_c_binding,only:c_int_fast8_t
use iso_c_binding,only:c_int_least16_t
use iso_c_binding,only:c_int_fast16_t
use iso_c_binding,only:c_int_least32_t
use iso_c_binding,only:c_int_fast32_t
use iso_c_binding,only:c_int_least64_t
use iso_c_binding,only:c_int_fast64_t
use iso_c_binding,only:c_int_least128_t
use iso_c_binding,only:c_int_fast128_t
use iso_c_binding,only:c_float
use iso_c_binding,only:c_double
use iso_c_binding,only:c_long_double
use iso_c_binding,only:c_float_complex
use iso_c_binding,only:c_double_complex
use iso_c_binding,only:c_long_double_complex
use iso_c_binding,only:c_bool
use iso_c_binding,only:c_char
use iso_c_binding,only:c_null_char
use iso_c_binding,only:c_alert
use iso_c_binding,only:c_backspace
use iso_c_binding,only:c_form_feed
use iso_c_binding,only:c_new_line
use iso_c_binding,only:c_carriage_return
use iso_c_binding,only:c_horizontal_tab
use iso_c_binding,only:c_vertical_tab
use iso_c_binding,only:c_float128
use iso_c_binding,only:c_float128_complex
use iso_c_binding,only:c_uint8_t
use iso_c_binding,only:c_uint16_t
use iso_c_binding,only:c_uint32_t
use iso_c_binding,only:c_uint64_t
use iso_c_binding,only:c_uint128_t
use iso_c_binding,only:c_unsigned_char
use iso_c_binding,only:c_unsigned_short
use iso_c_binding,only:c_unsigned
use iso_c_binding,only:c_unsigned_long
use iso_c_binding,only:c_unsigned_long_long
use iso_c_binding,only:c_uintmax_t
use iso_c_binding,only:c_uint_fast8_t
use iso_c_binding,only:c_uint_fast16_t
use iso_c_binding,only:c_uint_fast32_t
use iso_c_binding,only:c_uint_fast64_t
use iso_c_binding,only:c_uint_fast128_t
use iso_c_binding,only:c_uint_least8_t
use iso_c_binding,only:c_uint_least16_t
use iso_c_binding,only:c_uint_least32_t
use iso_c_binding,only:c_uint_least64_t
use iso_c_binding,only:c_uint_least128_t
use iso_c_binding,only:c_f_procpointer
contains
subroutine lapacke_dgetrf(matrix_layout,m,n,a,lda,ipiv) bind(c,name="LAPACKE_dgetrf")
integer(4),value::matrix_layout
integer(4),value::m
integer(4),value::n
real(8)::a(1_8:*)
integer(4),value::lda
integer(4)::ipiv(1_8:*)
end
end
