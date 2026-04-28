# Fortran–C Cross-Language Interface Validator

A tool to detect type mismatches, ABI violations, parameter count/order errors, and pointer/value passing mismatches across the Fortran–C boundary with precise source locations.

## Project Goal
To build a command-line tool that accepts `<fortran_file.f90>` and `<c_header.h>` as input, parses their respective `BIND(C)` interfaces and C header definitions, and outputs a detailed compatibility report.

## Features
-   Parse Fortran `BIND(C)` interfaces (using a restricted parser, extendable to Flang).
-   Parse C header files using Clang AST.
-   Compare function names, parameter counts, order, types, pointer/value passing, structs, and arrays.
-   Generate colorful, human-readable terminal output.
-   Optionally generate machine-readable JSON reports.

## Installation

1.  **Clone the repository (after exporting from Colab):**
    ```bash
    git clone https://github.com/yourusername/fc-validator.git
    cd fc-validator
    ```

2.  **Install system dependencies:**
    This tool relies on `clang` and `gfortran` to be installed on your system. `jq` is also useful for processing JSON output.
    ```bash
    sudo apt-get update
    sudo apt-get install -y clang gfortran jq
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install .
    ```

## Usage

### Basic Validation
```bash
fc-validator <path_to_fortran_file.f90> <path_to_c_header.h>
```

### JSON Output
```bash
fc-validator <path_to_fortran_file.f90> <path_to_c_header.h> --json > report.json
```

## Development

### Running Tests
```bash
pytest
```

### Code Structure
-   `fc_validator/cli.py`: Command-line interface definition.
-   `fc_validator/fortran_parser.py`: Fortran source code parsing logic.
-   `fc_validator/c_parser.py`: C header parsing via Clang.
-   `fc_validator/compare.py`: Core logic for comparing Fortran and C models.
-   `fc_validator/report.py`: Output formatting for terminal and JSON reports.
-   `fc_validator/utils.py`: Helper utilities.

## License
This project is licensed under the MIT License.
