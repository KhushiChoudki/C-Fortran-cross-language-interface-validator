import { useState, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { Play, Terminal, Copy, CheckCircle, XCircle, ChevronRight, ListChecks } from 'lucide-react';
import axios from 'axios';

// ─── All 32 test cases hardcoded with descriptions ──────────────────────────
const ALL_TEST_CASES = [
  {
    id: 'mismatch_scalar',
    label: 'Scalar Type Mismatch',
    category: 'Type Mismatch',
    description: 'C declares int, Fortran uses real(8). Silent ABI bug — same register, different interpretation.',
    c_code: `void sub(int x);`,
    f_code: `subroutine sub(x) bind(c)\n  real(8) :: x\nend subroutine`,
  },
  {
    id: 'mismatch_count',
    label: 'Parameter Count Mismatch',
    category: 'Parameter Error',
    description: 'C declares two parameters (x, y), Fortran only declares one. Stack corruption at runtime.',
    c_code: `void sub(int x, int y);`,
    f_code: `subroutine sub(x) bind(c)\n  integer(4) :: x\nend subroutine`,
  },
  {
    id: 'mismatch_passby_1',
    label: 'Pass-by-Value vs Reference (int)',
    category: 'Passing Convention',
    description: 'C passes int by value but Fortran expects it by reference (no VALUE). Pointer dereference on a scalar.',
    c_code: `void sub(int x);`,
    f_code: `subroutine sub(x) bind(c)\n  integer(4) :: x\nend subroutine`,
  },
  {
    id: 'mismatch_passby_2',
    label: 'Pass-by-Reference vs Value (int*)',
    category: 'Passing Convention',
    description: 'C passes int* (pointer) but Fortran has VALUE — it receives the pointer address as an integer instead of dereferencing.',
    c_code: `void sub(int *x);`,
    f_code: `subroutine sub(x) bind(c)\n  integer(4), value :: x\nend subroutine`,
  },
  {
    id: 'mismatch_name',
    label: 'BIND(C) Name Mismatch',
    category: 'Name Binding',
    description: 'C function is sub_c but Fortran BIND(C, name="wrong_name"). Linker will fail to resolve the symbol.',
    c_code: `void sub_c(int x);`,
    f_code: `subroutine sub(x) bind(c, name="wrong_name")\n  integer(4) :: x\nend subroutine`,
  },
  {
    id: 'mismatch_struct',
    label: 'Struct Field Type Mismatch',
    category: 'Struct Layout',
    description: 'C struct has double y but Fortran maps y as integer(c_int). Struct layout and ABI are broken.',
    c_code: `struct my_struct {\n    int x;\n    double y;\n};\nvoid sub(struct my_struct s);`,
    f_code: `module struct_mod\n  use iso_c_binding\n  type, bind(c) :: my_struct\n    integer(c_int) :: x\n    integer(c_int) :: y ! Mismatch: C has double\n  end type\ncontains\n  subroutine sub(s) bind(c)\n    type(my_struct), value :: s\n  end subroutine\nend module`,
  },
  {
    id: 'case_6',
    label: '_Bool vs logical(4)',
    category: 'Type Mismatch',
    description: 'C _Bool is 1 byte; Fortran logical(4) is 4 bytes. Interop requires logical(c_bool) — wrong kind causes size mismatch.',
    c_code: `void sub_6(_Bool x);`,
    f_code: `module test_mod_6\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_6(x) bind(c)\n    logical(4), value :: x\n  end subroutine\nend module`,
  },
  {
    id: 'case_7',
    label: 'float vs real(c_double)',
    category: 'Type Mismatch',
    description: 'C float (32-bit) mapped to Fortran real(c_double) (64-bit). Precision doubled silently.',
    c_code: `void sub_7(float x);`,
    f_code: `module test_mod_7\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_7(x) bind(c)\n    real(c_double), value :: x\n  end subroutine\nend module`,
  },
  {
    id: 'case_8',
    label: 'short vs integer(c_int)',
    category: 'Type Mismatch',
    description: 'C short (16-bit) vs Fortran integer(c_int) (32-bit). Extra bytes read from stack — classic ABI bug.',
    c_code: `void sub_8(short x);`,
    f_code: `module test_mod_8\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_8(x) bind(c)\n    integer(c_int), value :: x\n  end subroutine\nend module`,
  },
  {
    id: 'case_9',
    label: 'long vs integer(c_int)',
    category: 'Type Mismatch',
    description: 'C long may be 64-bit on Linux but Fortran uses c_int (32-bit). Platform-dependent silent truncation.',
    c_code: `void sub_9(long x);`,
    f_code: `module test_mod_9\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_9(x) bind(c)\n    integer(c_int), value :: x\n  end subroutine\nend module`,
  },
  {
    id: 'case_10',
    label: 'Struct Missing Field',
    category: 'Struct Layout',
    description: 'C struct has {int x, double y} but Fortran only declares x. Field y missing — struct size mismatch.',
    c_code: `struct my_struct_10 { int x; double y; };\nvoid sub_10(struct my_struct_10 s);`,
    f_code: `module struct_mod_10\n  use iso_c_binding\n  implicit none\n  type, bind(c) :: my_struct_10\n    integer(c_int) :: x\n  end type\ncontains\n  subroutine sub_10(s) bind(c)\n    type(my_struct_10), value :: s\n  end subroutine\nend module`,
  },
  {
    id: 'case_11',
    label: 'Struct Field Wrong Type',
    category: 'Struct Layout',
    description: 'C struct {int x, double y} — Fortran maps y as integer(c_int) instead of real(c_double). Size and bit pattern differ.',
    c_code: `struct my_struct_11 { int x; double y; };\nvoid sub_11(struct my_struct_11 s);`,
    f_code: `module struct_mod_11\n  use iso_c_binding\n  implicit none\n  type, bind(c) :: my_struct_11\n    integer(c_int) :: x\n    integer(c_int) :: y\n  end type\ncontains\n  subroutine sub_11(s) bind(c)\n    type(my_struct_11), value :: s\n  end subroutine\nend module`,
  },
  {
    id: 'case_12',
    label: 'Struct Field Order Swapped',
    category: 'Struct Layout',
    description: 'C struct fields are {int x, double y}; Fortran reverses them to {y, x}. ABI layout broken — alignment padding differs.',
    c_code: `struct my_struct_12 { int x; double y; };\nvoid sub_12(struct my_struct_12 s);`,
    f_code: `module struct_mod_12\n  use iso_c_binding\n  implicit none\n  type, bind(c) :: my_struct_12\n    real(c_double) :: y\n    integer(c_int) :: x\n  end type\ncontains\n  subroutine sub_12(s) bind(c)\n    type(my_struct_12), value :: s\n  end subroutine\nend module`,
  },
  {
    id: 'case_13',
    label: 'const int* vs VALUE int',
    category: 'Passing Convention',
    description: 'C passes const int* (pointer), Fortran uses VALUE integer(c_int). Pointer coerced to integer — undefined behaviour.',
    c_code: `void sub_13(const int *x);`,
    f_code: `module test_mod_13\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_13(x) bind(c)\n    integer(c_int), value :: x\n  end subroutine\nend module`,
  },
  {
    id: 'case_14',
    label: 'char* vs character VALUE',
    category: 'String / Char',
    description: 'C passes char* (pointer to string), Fortran receives a single character VALUE. Pointer vs scalar mismatch.',
    c_code: `void sub_14(char *s);`,
    f_code: `module test_mod_14\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_14(s) bind(c)\n    character(kind=c_char), value :: s\n  end subroutine\nend module`,
  },
  {
    id: 'case_15',
    label: 'void* vs integer VALUE',
    category: 'Pointer Mismatch',
    description: 'C void* (generic pointer) received as Fortran integer(c_int) VALUE. Pointer-as-integer ABI violation.',
    c_code: `void sub_15(void *ptr);`,
    f_code: `module test_mod_15\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_15(ptr) bind(c)\n    integer(c_int), value :: ptr\n  end subroutine\nend module`,
  },
  {
    id: 'case_16',
    label: 'double** vs real(c_double) VALUE',
    category: 'Pointer Mismatch',
    description: 'C double** (pointer-to-pointer) vs Fortran real(c_double) VALUE. Double-indirection completely lost.',
    c_code: `void sub_16(double **ptr);`,
    f_code: `module test_mod_16\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_16(ptr) bind(c)\n    real(c_double), value :: ptr\n  end subroutine\nend module`,
  },
  {
    id: 'case_17',
    label: 'int arr[10] vs scalar VALUE',
    category: 'Array Mismatch',
    description: 'C int arr[10] (array decays to pointer) vs Fortran integer VALUE scalar. Array vs scalar — whole pointer lost.',
    c_code: `void sub_17(int arr[10]);`,
    f_code: `module test_mod_17\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_17(arr) bind(c)\n    integer(c_int), value :: arr\n  end subroutine\nend module`,
  },
  {
    id: 'case_18',
    label: 'Function Return Type Mismatch',
    category: 'Return Type',
    description: 'C declares double return but Fortran is a subroutine (void return). Return value register undefined.',
    c_code: `double sub_18(int x);`,
    f_code: `module test_mod_18\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_18(x) bind(c)\n    integer(c_int), value :: x\n  end subroutine\nend module`,
  },
  {
    id: 'case_19',
    label: 'Parameter Order Swapped',
    category: 'Parameter Error',
    description: 'C declares (rows, cols) but Fortran declares (cols, rows). Arguments silently swapped at call site.',
    c_code: `void sub_19(int rows, int cols);`,
    f_code: `module test_mod_19\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_19(cols, rows) bind(c)\n    integer(c_int), value :: cols\n    integer(c_int), value :: rows\n  end subroutine\nend module`,
  },
  {
    id: 'case_20',
    label: 'double* Missing VALUE',
    category: 'Passing Convention',
    description: 'C double* (pointer passed by value) but Fortran real(c_double) has no VALUE — Fortran gets a reference-to-pointer.',
    c_code: `void sub_20(double *data);`,
    f_code: `module test_mod_20\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_20(data) bind(c)\n    real(c_double) :: data\n  end subroutine\nend module`,
  },
  {
    id: 'case_21',
    label: 'float _Complex vs real(c_float)',
    category: 'Type Mismatch',
    description: 'C float _Complex is 8 bytes (real+imag), Fortran real(c_float) is 4 bytes. Complex type completely ignored.',
    c_code: `void sub_21(float _Complex z);`,
    f_code: `module test_mod_21\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_21(z) bind(c)\n    real(c_float), value :: z\n  end subroutine\nend module`,
  },
  {
    id: 'case_22',
    label: 'Struct int field vs real(c_double)',
    category: 'Struct Layout',
    description: 'C struct {int val} — Fortran maps val as real(c_double). 4-byte int interpreted as 8-byte float.',
    c_code: `struct val_struct_22 { int val; };\nvoid sub_22(struct val_struct_22 s);`,
    f_code: `module struct_mod_22\n  use iso_c_binding\n  implicit none\n  type, bind(c) :: val_struct_22\n    real(c_double) :: val\n  end type\ncontains\n  subroutine sub_22(s) bind(c)\n    type(val_struct_22), value :: s\n  end subroutine\nend module`,
  },
  {
    id: 'case_23',
    label: 'char VALUE Missing',
    category: 'Passing Convention',
    description: 'C char passed by value; Fortran character(kind=c_char) has no VALUE — treated as reference.',
    c_code: `void sub_23(char c);`,
    f_code: `module test_mod_23\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_23(c) bind(c)\n    character(kind=c_char) :: c\n  end subroutine\nend module`,
  },
  {
    id: 'case_24',
    label: 'short vs integer(c_double)',
    category: 'Type Mismatch',
    description: 'C short (2 bytes) mapped to Fortran integer(c_double) — c_double kind is not a valid integer kind, size wildly wrong.',
    c_code: `void sub_24(short val);`,
    f_code: `module test_mod_24\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_24(val) bind(c)\n    integer(c_double), value :: val\n  end subroutine\nend module`,
  },
  {
    id: 'case_25',
    label: 'long long vs integer(c_short)',
    category: 'Type Mismatch',
    description: 'C long long (8 bytes) vs Fortran integer(c_short) (2 bytes). Drastic size mismatch — upper 6 bytes truncated.',
    c_code: `void sub_25(long long val);`,
    f_code: `module test_mod_25\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_25(val) bind(c)\n    integer(c_short), value :: val\n  end subroutine\nend module`,
  },
  {
    id: 'case_26',
    label: 'float* vs real(c_double) VALUE',
    category: 'Pointer Mismatch',
    description: 'C float* (pointer) vs Fortran real(c_double) VALUE — pointer passed where a double scalar is expected.',
    c_code: `void sub_26(float *val);`,
    f_code: `module test_mod_26\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_26(val) bind(c)\n    real(c_double), value :: val\n  end subroutine\nend module`,
  },
  {
    id: 'case_27',
    label: 'double Value Missing in Fortran',
    category: 'Passing Convention',
    description: 'C double passed by value but Fortran real(c_double) has no VALUE attribute — reference semantics applied to value argument.',
    c_code: `void sub_27(double val);`,
    f_code: `module test_mod_27\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_27(val) bind(c)\n    real(c_double) :: val\n  end subroutine\nend module`,
  },
  {
    id: 'case_28',
    label: '2D Array vs scalar VALUE',
    category: 'Array Mismatch',
    description: 'C float matrix[3][5] (array, decays to pointer) vs Fortran real(c_float) VALUE scalar. Multidimensional array collapsed to scalar.',
    c_code: `void sub_28(float matrix[3][5]);`,
    f_code: `module test_mod_28\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_28(matrix) bind(c)\n    real(c_float), value :: matrix\n  end subroutine\nend module`,
  },
  {
    id: 'case_29',
    label: 'size_t vs integer(c_short)',
    category: 'Type Mismatch',
    description: 'C size_t (platform pointer-size, 8 bytes on 64-bit) vs Fortran integer(c_short) (2 bytes). Size mismatch on 64-bit platforms.',
    c_code: `void sub_29(size_t n);`,
    f_code: `module test_mod_29\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_29(n) bind(c)\n    integer(c_short), value :: n\n  end subroutine\nend module`,
  },
  {
    id: 'case_30',
    label: 'unsigned int vs integer(c_short)',
    category: 'Type Mismatch',
    description: 'C unsigned int (4 bytes) vs Fortran integer(c_short) (2 bytes). Sign and width both wrong.',
    c_code: `void sub_30(unsigned int x);`,
    f_code: `module test_mod_30\n  use iso_c_binding\n  implicit none\ncontains\n  subroutine sub_30(x) bind(c)\n    integer(c_short), value :: x\n  end subroutine\nend module`,
  },
  {
    id: 'case_31',
    label: 'Nested Struct Field Mismatch',
    category: 'Struct Layout',
    description: 'C has nested structs: outer_s {inner_s {int val}}. Fortran inner type maps val as real(c_double) — nested layout corrupted.',
    c_code: `struct inner_s { int val; };\nstruct outer_s { struct inner_s inner; };\nvoid sub_31(struct outer_s s);`,
    f_code: `module struct_mod_31\n  use iso_c_binding\n  implicit none\n  type, bind(c) :: inner_s\n    real(c_double) :: val\n  end type\n  type, bind(c) :: outer_s\n    type(inner_s) :: inner\n  end type\ncontains\n  subroutine sub_31(s) bind(c)\n    type(outer_s), value :: s\n  end subroutine\nend module`,
  },
];

const CATEGORY_COLORS = {
  'Type Mismatch':      { bg: 'rgba(239,68,68,0.12)',   border: '#ef4444', text: '#f87171' },
  'Parameter Error':    { bg: 'rgba(249,115,22,0.12)',  border: '#f97316', text: '#fb923c' },
  'Passing Convention': { bg: 'rgba(234,179,8,0.12)',   border: '#eab308', text: '#fbbf24' },
  'Struct Layout':      { bg: 'rgba(168,85,247,0.12)',  border: '#a855f7', text: '#c084fc' },
  'Pointer Mismatch':   { bg: 'rgba(59,130,246,0.12)',  border: '#3b82f6', text: '#60a5fa' },
  'Array Mismatch':     { bg: 'rgba(20,184,166,0.12)',  border: '#14b8a6', text: '#2dd4bf' },
  'String / Char':      { bg: 'rgba(236,72,153,0.12)',  border: '#ec4899', text: '#f472b6' },
  'Return Type':        { bg: 'rgba(16,185,129,0.12)',  border: '#10b981', text: '#34d399' },
  'Name Binding':       { bg: 'rgba(99,102,241,0.12)',  border: '#6366f1', text: '#818cf8' },
};

const CATEGORIES = ['All', ...Object.keys(CATEGORY_COLORS)];

export default function TestCasesTab() {
  const [selectedCase, setSelectedCase] = useState(null);
  const [cCode, setCCode] = useState('');
  const [fCode, setFCode] = useState('');
  const [runningId, setRunningId] = useState(null);      // which case is being validated
  const [cliRunningId, setCliRunningId] = useState(null); // which case runs CLI
  const [results, setResults] = useState({});            // { caseId: { errors, cliOutput, cliCommand, consoleTab } }
  const [batchRunning, setBatchRunning] = useState(false);
  const [filterCategory, setFilterCategory] = useState('All');
  const [copied, setCopied] = useState(null);

  const cEditorRef = useRef(null);
  const fEditorRef = useRef(null);
  const monacoRef = useRef(null);

  const handleEditorDidMount = (editor, monaco, type) => {
    if (type === 'c') cEditorRef.current = editor;
    if (type === 'f') fEditorRef.current = editor;
    if (!monacoRef.current) monacoRef.current = monaco;
  };

  const openCase = (tc) => {
    setSelectedCase(tc);
    setCCode(tc.c_code);
    setFCode(tc.f_code);
  };

  const closePanel = () => {
    setSelectedCase(null);
    setCCode('');
    setFCode('');
  };

  const handleValidate = async (tc) => {
    setRunningId(tc.id);
    const codeToValidate = {
      c_code: selectedCase?.id === tc.id ? cCode : tc.c_code,
      fortran_code: selectedCase?.id === tc.id ? fCode : tc.f_code,
    };
    try {
      const response = await axios.post('http://127.0.0.1:5000/api/validate', codeToValidate);
      const errors = response.data.results || [];
      setResults(prev => ({
        ...prev,
        [tc.id]: { ...prev[tc.id], errors, consoleTab: 'validation' }
      }));
      if (selectedCase?.id === tc.id) applyMarkers(errors);
    } catch (e) {
      const errMsg = e.response?.data?.error
        ? `Backend error: ${e.response.data.error}`
        : `Cannot reach backend (is server.py running?): ${e.message}`;
      setResults(prev => ({
        ...prev,
        [tc.id]: { ...prev[tc.id], errors: [{ level: 'ERROR', msg: errMsg, loc: 'Network' }], consoleTab: 'validation' }
      }));
    } finally {
      setRunningId(null);
    }
  };

  const handleRunCli = async (tc) => {
    setCliRunningId(tc.id);
    setResults(prev => ({ ...prev, [tc.id]: { ...prev[tc.id], consoleTab: 'cli' } }));
    try {
      const response = await axios.post('http://127.0.0.1:5000/api/cli-run', {
        c_code: tc === selectedCase ? cCode : tc.c_code,
        fortran_code: tc === selectedCase ? fCode : tc.f_code,
        case_name: tc.id,
      });
      setResults(prev => ({
        ...prev,
        [tc.id]: { ...prev[tc.id], cliOutput: response.data.output, cliCommand: response.data.command, consoleTab: 'cli' }
      }));
    } catch (e) {
      setResults(prev => ({
        ...prev,
        [tc.id]: { ...prev[tc.id], cliOutput: 'Error: ' + e.message, consoleTab: 'cli' }
      }));
    } finally {
      setCliRunningId(null);
    }
  };

  const applyMarkers = (errors) => {
    if (!monacoRef.current) return;
    const cMarkers = [], fMarkers = [];
    const monaco = monacoRef.current;
    errors.forEach(issue => {
      const severity = issue.level === 'ERROR' ? monaco.MarkerSeverity.Error : monaco.MarkerSeverity.Warning;
      const cMatch = (issue.loc || '').match(/C:.*:(\d+)/);
      if (cMatch) { let l = parseInt(cMatch[1]) || 1; cMarkers.push({ startLineNumber: l, startColumn: 1, endLineNumber: l, endColumn: 100, message: issue.msg, severity }); }
      const fMatch = (issue.loc || '').match(/Fortran line (\d+|\?)/);
      if (fMatch) { let l = parseInt(fMatch[1]) || 1; fMarkers.push({ startLineNumber: l, startColumn: 1, endLineNumber: l, endColumn: 100, message: issue.msg, severity }); }
    });
    if (cEditorRef.current) monaco.editor.setModelMarkers(cEditorRef.current.getModel(), 'validator', cMarkers);
    if (fEditorRef.current) monaco.editor.setModelMarkers(fEditorRef.current.getModel(), 'validator', fMarkers);
  };

  const handleRunAll = async () => {
    setBatchRunning(true);
    for (const tc of ALL_TEST_CASES) {
      setRunningId(tc.id);
      try {
        const response = await axios.post('http://127.0.0.1:5000/api/validate', {
          c_code: tc.c_code, fortran_code: tc.f_code,
        });
        const errors = response.data.results || [];
        setResults(prev => ({ ...prev, [tc.id]: { ...prev[tc.id], errors, consoleTab: 'validation' } }));
      } catch (e) {
        const errMsg = e.response?.data?.error
          ? `Backend error: ${e.response.data.error}`
          : `Cannot reach backend: ${e.message}`;
        setResults(prev => ({ ...prev, [tc.id]: { ...prev[tc.id], errors: [{ level: 'ERROR', msg: errMsg, loc: 'Network' }], consoleTab: 'validation' } }));
      }
    }
    setRunningId(null);
    setBatchRunning(false);
  };

  const copyCmd = (cmd, id) => {
    navigator.clipboard.writeText(cmd);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const setConsoleTab = (id, tab) => {
    setResults(prev => ({ ...prev, [id]: { ...prev[id], consoleTab: tab } }));
  };

  const filtered = filterCategory === 'All' ? ALL_TEST_CASES : ALL_TEST_CASES.filter(tc => tc.category === filterCategory);

  const passCount = Object.values(results).filter(r => r.errors && r.errors.length === 0).length;
  const failCount = Object.values(results).filter(r => r.errors && r.errors.length > 0).length;
  const totalRan = passCount + failCount;

  return (
    <div className="test-cases-tab" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>

      {/* ── Header bar ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem 1.25rem', borderBottom: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.15)', flexShrink: 0, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1 }}>
          <ListChecks size={18} color="var(--accent)" />
          <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
            {ALL_TEST_CASES.length} Test Cases
          </span>
          {totalRan > 0 && (
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginLeft: '0.5rem' }}>
              — <span style={{ color: '#10b981' }}>{passCount} passed</span>
              {failCount > 0 && <span style={{ color: '#ef4444' }}>, {failCount} failed</span>}
              {' '}/ {totalRan} run
            </span>
          )}
        </div>

        {/* Category filter */}
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          {CATEGORIES.map(cat => {
            const col = cat === 'All' ? null : CATEGORY_COLORS[cat];
            const active = filterCategory === cat;
            return (
              <button
                key={cat}
                onClick={() => setFilterCategory(cat)}
                style={{
                  padding: '0.25rem 0.6rem', borderRadius: '999px', fontSize: '0.72rem', fontWeight: 600,
                  cursor: 'pointer', border: active ? `1.5px solid ${col?.border || 'var(--accent)'}` : '1.5px solid transparent',
                  background: active ? (col?.bg || 'rgba(99,179,237,0.15)') : 'rgba(255,255,255,0.05)',
                  color: active ? (col?.text || 'var(--accent)') : 'var(--text-secondary)',
                  transition: 'all 0.15s',
                }}
              >{cat}</button>
            );
          })}
        </div>

        <button
          className={`btn ${batchRunning ? 'loading' : ''}`}
          onClick={handleRunAll}
          disabled={batchRunning}
          style={{ flexShrink: 0 }}
        >
          {batchRunning ? <span className="spinner">⟳</span> : <ListChecks size={15} />}
          Run All
        </button>
      </div>

      {/* ── Body: card grid + optional side panel ── */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* Card grid */}
        <div style={{ flex: selectedCase ? '0 0 380px' : 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', borderRight: selectedCase ? '1px solid var(--border-color)' : 'none', transition: 'flex 0.2s' }}>
          {filtered.map((tc, idx) => {
            const r = results[tc.id];
            const isRunning = runningId === tc.id;
            const isCliRun = cliRunningId === tc.id;
            const col = CATEGORY_COLORS[tc.category] || CATEGORY_COLORS['Type Mismatch'];
            const hasResult = r?.errors !== undefined;
            const passed = hasResult && r.errors.length === 0;
            const failed = hasResult && r.errors.length > 0;
            const isOpen = selectedCase?.id === tc.id;

            return (
              <div
                key={tc.id}
                style={{
                  background: isOpen ? 'rgba(99,179,237,0.07)' : 'var(--surface)',
                  border: `1px solid ${isOpen ? 'var(--accent)' : failed ? '#ef444450' : passed ? '#10b98150' : 'var(--border-color)'}`,
                  borderRadius: '10px', padding: '0.85rem 1rem', cursor: 'pointer',
                  transition: 'all 0.15s', position: 'relative',
                }}
                onClick={() => isOpen ? closePanel() : openCase(tc)}
              >
                {/* Top row */}
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.4rem' }}>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-secondary)', opacity: 0.6, marginTop: '2px', minWidth: '22px' }}>
                    #{String(idx + 1).padStart(2, '0')}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-primary)' }}>{tc.label}</span>
                      <span style={{ fontSize: '0.68rem', fontWeight: 600, padding: '0.15rem 0.5rem', borderRadius: '999px', background: col.bg, color: col.text, border: `1px solid ${col.border}40` }}>
                        {tc.category}
                      </span>
                      {passed && <CheckCircle size={14} color="#10b981" />}
                      {failed && <XCircle size={14} color="#ef4444" />}
                      {(isRunning || isCliRun) && <span className="spinner" style={{ fontSize: '12px' }}>⟳</span>}
                    </div>
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: '0.25rem 0 0', lineHeight: 1.45 }}>{tc.description}</p>
                  </div>
                  <ChevronRight size={15} color="var(--text-secondary)" style={{ flexShrink: 0, transform: isOpen ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s' }} />
                </div>

                {/* Action buttons */}
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }} onClick={e => e.stopPropagation()}>
                  <button
                    className={`btn secondary`}
                    disabled={isCliRun || isRunning}
                    style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem', gap: '0.3rem' }}
                    onClick={(e) => { e.stopPropagation(); handleRunCli(tc); }}
                  >
                    {isCliRun ? <span className="spinner">⟳</span> : <Terminal size={13} />}
                    CLI
                  </button>
                  <button
                    className={`btn`}
                    disabled={isRunning || isCliRun}
                    style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem', gap: '0.3rem' }}
                    onClick={(e) => { e.stopPropagation(); handleValidate(tc); }}
                  >
                    {isRunning ? <span className="spinner">⟳</span> : <Play size={13} />}
                    Run
                  </button>
                </div>

                {/* Inline result panel */}
                {r && (r.errors !== undefined || r.cliOutput !== undefined) && (
                  <div style={{ marginTop: '0.65rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.6rem' }} onClick={e => e.stopPropagation()}>
                    {/* Console tabs */}
                    <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.5rem' }}>
                      {r.errors !== undefined && (
                        <button
                          style={{ fontSize: '0.7rem', fontWeight: 600, padding: '0.2rem 0.55rem', borderRadius: '6px', border: 'none', cursor: 'pointer', background: r.consoleTab !== 'cli' ? 'var(--accent)' : 'rgba(255,255,255,0.07)', color: r.consoleTab !== 'cli' ? '#fff' : 'var(--text-secondary)' }}
                          onClick={() => setConsoleTab(tc.id, 'validation')}
                        >Validation</button>
                      )}
                      {r.cliOutput !== undefined && (
                        <button
                          style={{ fontSize: '0.7rem', fontWeight: 600, padding: '0.2rem 0.55rem', borderRadius: '6px', border: 'none', cursor: 'pointer', background: r.consoleTab === 'cli' ? 'var(--accent)' : 'rgba(255,255,255,0.07)', color: r.consoleTab === 'cli' ? '#fff' : 'var(--text-secondary)' }}
                          onClick={() => setConsoleTab(tc.id, 'cli')}
                        >CLI Output</button>
                      )}
                    </div>

                    {r.consoleTab !== 'cli' && r.errors !== undefined && (
                      r.errors.length === 0 ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#10b981', fontSize: '0.8rem', fontWeight: 600 }}>
                          <CheckCircle size={14} /> All checks passed
                        </div>
                      ) : (
                        <ul style={{ margin: 0, padding: '0 0 0 1rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                          {r.errors.map((err, i) => (
                            <li key={i} style={{ marginBottom: '0.25rem', lineHeight: 1.4 }}>
                              <span style={{ color: err.level === 'ERROR' ? '#f87171' : '#fbbf24', fontWeight: 700 }}>{err.level}:</span>{' '}
                              {err.msg}
                              {err.loc && <span style={{ opacity: 0.6 }}> — {err.loc}</span>}
                            </li>
                          ))}
                        </ul>
                      )
                    )}

                    {r.consoleTab === 'cli' && r.cliOutput !== undefined && (
                      <div>
                        {r.cliCommand && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem', fontSize: '0.72rem', color: 'var(--text-secondary)', fontFamily: 'monospace', wordBreak: 'break-all' }}>
                            <span style={{ color: 'var(--accent)' }}>$</span> {r.cliCommand}
                            <button onClick={() => copyCmd(r.cliCommand, tc.id)} style={{ flexShrink: 0, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: '0.7rem' }}>
                              {copied === tc.id ? '✓ Copied' : <><Copy size={11} /> Copy</>}
                            </button>
                          </div>
                        )}
                        <pre style={{ margin: 0, fontSize: '0.72rem', color: '#a3e635', background: 'rgba(0,0,0,0.35)', borderRadius: '6px', padding: '0.6rem 0.75rem', overflowX: 'auto', maxHeight: '160px', overflowY: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                          {r.cliOutput}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* ── Side panel: code viewer ── */}
        {selectedCase && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--surface)' }}>
            {/* Panel header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.65rem 1rem', borderBottom: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.15)', flexShrink: 0 }}>
              <div style={{ flex: 1 }}>
                <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>{selectedCase.label}</span>
                <span style={{ marginLeft: '0.5rem', fontSize: '0.72rem', color: CATEGORY_COLORS[selectedCase.category]?.text, background: CATEGORY_COLORS[selectedCase.category]?.bg, padding: '0.15rem 0.5rem', borderRadius: '999px' }}>{selectedCase.category}</span>
              </div>
              <button
                className="btn secondary"
                style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}
                onClick={() => handleRunCli(selectedCase)}
                disabled={cliRunningId === selectedCase.id || runningId === selectedCase.id}
              >
                {cliRunningId === selectedCase.id ? <span className="spinner">⟳</span> : <Terminal size={13} />} CLI
              </button>
              <button
                className="btn"
                style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}
                onClick={() => handleValidate(selectedCase)}
                disabled={runningId === selectedCase.id || cliRunningId === selectedCase.id}
              >
                {runningId === selectedCase.id ? <span className="spinner">⟳</span> : <Play size={13} />} Validate
              </button>
              <button onClick={closePanel} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: 1 }}>✕</button>
            </div>

            {/* Editors */}
            <div className="editor-container" style={{ flex: 1 }}>
              <div className="editor-pane">
                <div className="editor-header">C Header (*.h)</div>
                <Editor
                  height="100%"
                  defaultLanguage="c"
                  theme="vs-dark"
                  value={cCode}
                  onChange={setCCode}
                  onMount={(ed, mo) => handleEditorDidMount(ed, mo, 'c')}
                  options={{ minimap: { enabled: false }, fontSize: 13 }}
                />
              </div>
              <div className="editor-pane">
                <div className="editor-header">Fortran Interface (*.f90)</div>
                <Editor
                  height="100%"
                  defaultLanguage="fortran"
                  theme="vs-dark"
                  value={fCode}
                  onChange={setFCode}
                  onMount={(ed, mo) => handleEditorDidMount(ed, mo, 'f')}
                  options={{ minimap: { enabled: false }, fontSize: 13 }}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
