
#ifndef LAPACKE_MINIMAL_H
#define LAPACKE_MINIMAL_H

typedef int lapack_int;

lapack_int LAPACKE_dgetrf( int matrix_layout, lapack_int m, lapack_int n,
                           double* a, lapack_int lda, lapack_int* ipiv );

#endif
