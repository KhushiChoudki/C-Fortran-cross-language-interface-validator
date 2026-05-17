<img width="1918" height="947" alt="image" src="https://github.com/user-attachments/assets/e2d51ec2-fcaf-4afb-ace8-11d68e704e8c" /># Fortran–C Cross-Language Interface Validator

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

## Web Application (UI)

The project now includes a beautiful, full-stack web application that provides a LeetCode-style experience for validating and generating Fortran-C interfaces.

### Features
- **IDE Validator Tab**: Dual Monaco editors with live syntax checking, semantic error squigglies, and a unified LeetCode-style test result console.
- **Test Cases Tab**: A comprehensive suite to browse, run, and batch-execute edge cases with an interactive sidebar.
- **AI Generator Tab**: Automatically generate Fortran `BIND(C)` interfaces from C headers using intelligent parsing.

### UI Screenshots

<img width="1911" height="899" alt="image" src="https://github.com/user-attachments/assets/7a24e301-b927-4858-af94-0cb048d345b0" />
*Figure 1: The IDE Validator showing a clean "Accepted" console after successful validation.*


<img width="1918" height="947" alt="image" src="https://github.com/user-attachments/assets/2baa948c-3415-4f91-bdbf-c2fa5a3a375c" />
*Figure 2: The IDE Validator catching multiple ABI violations and rendering them as red squiggly lines with a detailed "Wrong Answer" console.*


<img width="1919" height="925" alt="image" src="https://github.com/user-attachments/assets/dbad739d-aef4-414a-94fc-05c5c1a23051" />
*Figure 3: The AI Generator tab generating fortran subroutine for respective c header file*

## Project Structure

- `server.py`: Flask backend serving the API.
- `frontend/`: React + Vite frontend application.
- `fc_validator.py`: Main CLI entry point.
- `parsers/`: LLVM-based parsers for C and Fortran.
- `engine/`: Cross-language type comparison logic.
- `tests/`: Automated test suite with 30+ edge cases.
- `external/`: Real-world validation demo (LAPACKE).

## License

MIT
