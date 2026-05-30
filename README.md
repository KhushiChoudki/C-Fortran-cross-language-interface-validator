<img width="1918" height="947" alt="image" src="https://github.com/user-attachments/assets/e2d51ec2-fcaf-4afb-ace8-11d68e704e8c" />

# Fortran–C Cross-Language Interface Validator

A robust LLVM-powered validation engine and interactive web workspace designed to automatically detect type mismatches, ABI violations, and silent interoperability bugs between Fortran `BIND(C)` interfaces and their corresponding C headers.

---

## 📋 Assignment Overview: Assignment 20

### **Description**
A tool that parses Fortran `BIND(C)` interfaces via **Flang** and corresponding C headers via **Clang**, then cross-validates type compatibility, parameter passing, and struct layout — catching silent interop bugs before runtime compilation.

### **Background**
Mixed Fortran–C codebases (e.g., HPC libraries like LAPACK, PETSc, WRF) often rely on manual synchronization between Fortran interfaces and C headers. This process is highly error-prone, and no existing mainstream tool validates both sides simultaneously using actual compiler frontends. 

### **Objective**
Detect type mismatches, ABI violations, parameter count/order errors, and pointer/value passing mismatches across the Fortran–C boundary with precise, line-by-line source locations.

### **Deliverables**
1. **CLI Tool**: Accepts Fortran source and C header inputs, parsing both via LLVM frontends and outputting a comprehensive compatibility report.
2. **Type Comparison Engine**: Robust comparative validation covering scalars, structures/derived types, arrays, pointers, and strings.
3. **Test Suite**: A built-in validation suite containing **30+ deliberately mismatched interface pairs** to verify detector robustness.
4. **Real-world Verification**: Validation demonstration on standard HPC libraries, specifically demonstrating interop matching on LAPACKE structures and signatures.

---

## 🔍 Supported Mismatch Categories (Error Types)

This validator categorizes inter-language ABI and layout issues into **9 distinct error classes** exactly as represented in the interactive test suite:

| Category | Description | Severity | Example Issue Caught |
| :--- | :--- | :---: | :--- |
| **Type Mismatch** | Discrepancies between scalar types (e.g., size differences, float vs real double, logical kind errors). | `ERROR` / `WARNING` | C `int` (4 bytes) vs Fortran `real(8)` (8 bytes). |
| **Parameter Error** | Mismatches in argument count or swapped parameter order. | `ERROR` | C declares `(rows, cols)` but Fortran uses `(cols, rows)`. |
| **Passing Convention** | Mismatches between C pointer/value semantics and Fortran `VALUE` attributes. | `ERROR` | C passes `int` by value but Fortran expects reference (no `VALUE` attribute). |
| **Struct Layout** | Structural discrepancies: field count mismatches, reversed fields, alignment padding issues, or nested type compatibility issues. | `ERROR` | C `struct` has `{int x; double y;}` but Fortran swaps field order. |
| **Pointer Mismatch** | Incompatible pointer indirection levels (e.g. passing double-pointers where a scalar value is expected). | `ERROR` | C passes `double**` vs Fortran expects `real(8), value`. |
| **Array Mismatch** | Mismatches between arrays (which decay to pointers in C) and scalars or wrong dimensions. | `ERROR` | C passes `int arr[10]` vs Fortran expects a scalar `integer, value`. |
| **String / Char** | Incompatible character passing (e.g., pointer to string vs single char value). | `ERROR` | C passes `char *` vs Fortran expects single `character, value`. |
| **Return Type** | Discrepancies between C return type and Fortran subroutine vs function declaration. | `ERROR` | C function returns `double` but Fortran declares a `subroutine` (void return). |
| **Name Binding** | Symbol resolution failures between C function name and Fortran `BIND(C, name="...")` binding name. | `ERROR` | C function is `sub_c` but Fortran BIND(C) name is `"wrong_name"`. |

---

## 🚀 Installation & Prerequisites

### **1. Prerequisites**
- **Python 3.8+**
- **LLVM Toolchain** (requires `clang.exe` and `flang-new.exe`).
  - **On Windows**: Install via Winget in PowerShell:
    ```powershell
    winget install LLVM.LLVM
    ```

### **2. Setup & Installation**
```bash
git clone https://github.com/KhushiChoudki/C-Fortran-cross-language-interface-validator.git
cd C-Fortran-cross-language-interface-validator
```

---

## 💻 CLI Usage & Testing

Run the CLI tool by passing a Fortran source file and a C header:
```powershell
python fc_validator.py --fortran path/to/source.f90 --c path/to/header.h --clang "C:\Program Files\LLVM\bin\clang.exe" --flang "C:\Program Files\LLVM\bin\flang-new.exe"
```

### **Running the Deliberate Mismatches Test Suite (30+ Cases)**
Execute the suite of 32 edge cases to see the type comparison engine detect all errors:
```powershell
python scripts/run_all_tests.py
```

---

## 🎨 Interactive Web Application

A premium, full-stack LeetCode-style web interface is provided for live cross-language validation and generator pipelines.

### **Features**
1. **IDE Validator Tab**: Interactive side-by-side Monaco Editors for C and Fortran. When the interfaces are compatible, a clean green confirmation is rendered in the validation report console as shown in **Figure 1**. When type or passing mismatches are introduced, the comparative type engine highlights these errors directly inside the Monaco editors with line-specific squigglies and details them in the console report as illustrated in **Figure 2**. Furthermore, developers can run the raw command-line compilation dump inside the integrated console to inspect raw AST validation outputs directly from the web workspace as depicted in **Figure 5**.
2. **Test Cases Tab**: A comprehensive sidebar containing the **30+ built-in deliberate mismatches** to browse, run, and batch-execute edge cases with an interactive split-view editor showing side-by-side mismatch detail validation and accurate dynamic line number mapping, as cited in **Figure 4**.
3. **AI Generator Tab**: Automatically generates fully compatible Fortran `BIND(C)` modules and subprograms from pasted C headers in a conversational chat window, as shown in **Figure 3**.

### **Running the Web App Locally**

1. **Start the Flask Backend Server**:
   ```bash
   python server.py
   ```
2. **Start the Vite/React Frontend Server**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
3. Open your browser and navigate to **[http://localhost:5173/](http://localhost:5173/)** to access the workspace.

---

## 📸 Web Application Screenshots

<img width="1911" height="899" alt="image" src="https://github.com/user-attachments/assets/7a24e301-b927-4858-af94-0cb048d345b0" />
*Figure 1: The IDE Validator showing a clean "Accepted" console after successful validation.*


<img width="1918" height="947" alt="image" src="https://github.com/user-attachments/assets/2baa948c-3415-4f91-bdbf-c2fa5a3a375c" />
*Figure 2: The IDE Validator catching multiple ABI violations and rendering them as red squiggly lines with a detailed "Wrong Answer" console.*


<img width="1919" height="925" alt="image" src="https://github.com/user-attachments/assets/dbad739d-aef4-414a-94fc-05c5c1a23051" />
*Figure 3: The AI Generator tab generating a Fortran subroutine for the respective C header file.*


<img width="1920" height="960" alt="image" src="https://github.com/user-attachments/assets/YOUR_TEST_CASES_DETAIL_IMAGE_URL" />
*Figure 4: The Test Cases tab showing side-by-side interactive code validation with accurate dynamic line number mapping.*


<img width="1920" height="960" alt="image" src="https://github.com/user-attachments/assets/YOUR_CLI_TERMINAL_IMAGE_URL" />
*Figure 5: The CLI Terminal view within the IDE Validator tab displaying raw LLVM AST-dump verification outputs.*

---

## 📂 Project Structure

- `server.py`: Flask backend serving validation and generation APIs.
- `parsers/`: LLVM Clang-JSON and Flang-Symbols parsing libraries.
- `engine/`: Core type comparison comparator and semantic checker.
- `frontend/`: Vite-powered React front-end application.
- `tests/`: Directory containing the 32 deliberately mismatched test cases.
- `scripts/`: Test suites and setup scripts.
- `external/`: Real-world LAPACKE validation files.

## 📄 License
MIT
