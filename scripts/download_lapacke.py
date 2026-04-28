import urllib.request
import os

def download_file(url, dest):
    print(f"[*] Downloading {url}...")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"[+] Saved to {dest}")
    except Exception as e:
        print(f"[!] Failed: {e}")

def main():
    os.makedirs("external/lapacke", exist_ok=True)
    
    # LAPACKE headers and Fortran examples
    # These are small subsets for demonstration
    base_url = "https://raw.githubusercontent.com/Reference-LAPACK/lapack/master/LAPACKE/include/"
    headers = ["lapacke.h", "lapacke_config.h", "lapacke_mangle.h"]
    
    for h in headers:
        download_file(base_url + h, f"external/lapacke/{h}")

    # A sample Fortran interface file (simplified)
    with open("external/lapacke/lapack_interfaces.f90", "w") as f:
        f.write("""
subroutine LAPACKE_dgetrf( matrix_layout, m, n, a, lda, ipiv, info ) bind(c, name="LAPACKE_dgetrf")
  import :: c_int, c_double
  integer(c_int), value :: matrix_layout
  integer(c_int), value :: m
  integer(c_int), value :: n
  real(c_double) :: a(*)
  integer(c_int), value :: lda
  integer(c_int) :: ipiv(*)
  integer(c_int) :: info
end subroutine
""")

if __name__ == "__main__":
    main()
