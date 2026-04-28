# Fortran–C Cross-Language Interface Validator

A robust CLI tool designed to detect type mismatches, ABI violations, and silent interoperability bugs between Fortran `BIND(C)` interfaces and their corresponding C headers.

## Overview

Mixed-language codebases (e.g., LAPACK, PETSc, WRF) often rely on manual synchronization between Fortran interfaces and C headers. This tool automates the validation process by using actual compiler frontends (**Clang** for C and **Flang** for Fortran) to extract and compare metadata.

### Key Features

- **Scalar Type Validation**: Ensures `c_int`, `c_double`, etc., match their C counterparts (`int`, `double`).
- **Struct/Derived Type Layout**: Cross-validates field counts and types within C `structs` and Fortran `type, bind(c)`.
- **Pass-by-Attribute Check**: Detects mismatches between C pointers/values and Fortran `VALUE` attributes.
- **Argument Order & Count**: Precisely identifies errors in parameter lists.
- **LLVM-Powered**: Uses `clang -ast-dump=json` and `flang-new -fdebug-dump-symbols` for high-fidelity parsing.

## Installation

### Prerequisites

- **Python 3.8+**
- **LLVM/Clang/Flang**: The tool requires the LLVM toolchain. You can install it on Windows via Winget:
  ```powershell
  winget install LLVM.LLVM
  ```

### Setup

Clone the repository:
```bash
git clone https://github.com/KhushiChoudki/C-Fortran-cross-language-interface-validator.git
cd C-Fortran-cross-language-interface-validator
```

## Usage

Run the validator by providing the Fortran source and C header paths:

```powershell
python fc_validator.py --fortran path/to/source.f90 --c path/to/header.h --clang "C:\Program Files\LLVM\bin\clang.exe" --flang "C:\Program Files\LLVM\bin\flang-new.exe"
```

### Example: LAPACKE Validation

```powershell
python fc_validator.py --fortran external/lapacke/lapack_interfaces.f90 --c external/lapacke/lapacke_minimal.h
```

## Testing

The tool includes a suite of **30+ deliberately mismatched interface pairs** to verify its detection capabilities.

Run the full test suite:
```powershell
python scripts/run_all_tests.py
```

## Project Structure

- `fc_validator.py`: Main CLI entry point.
- `parsers/`: LLVM-based parsers for C and Fortran.
- `engine/`: Cross-language type comparison logic.
- `tests/`: Automated test suite with 30+ edge cases.
- `external/`: Real-world validation demo (LAPACKE).

## License

MIT
