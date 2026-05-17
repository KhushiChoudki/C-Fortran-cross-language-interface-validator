import { useState, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { Play, CheckCircle } from 'lucide-react';
import axios from 'axios';

const DEFAULT_C = `void do_math(int rows, int cols, double *matrix);
`;

const DEFAULT_F = `module test_mod
  use iso_c_binding
  implicit none
  interface
      subroutine do_math(cols, rows, matrix) bind(C, name="do_math")
          import :: c_int, c_double
          integer(c_int), value :: cols
          integer(c_int) :: rows ! Missing value, swapped name
          real(c_double) :: matrix
      end subroutine do_math
  end interface
end module test_mod
`;

export default function IDEValidatorTab() {
  const [cCode, setCCode] = useState(DEFAULT_C);
  const [fCode, setFCode] = useState(DEFAULT_F);
  const [isValidating, setIsValidating] = useState(false);
  const [validationErrors, setValidationErrors] = useState(null);
  
  const cEditorRef = useRef(null);
  const fEditorRef = useRef(null);
  const monacoRef = useRef(null);

  const handleEditorDidMount = (editor, monaco, type) => {
    if (type === 'c') cEditorRef.current = editor;
    if (type === 'f') fEditorRef.current = editor;
    if (!monacoRef.current) monacoRef.current = monaco;
  };

  const handleValidate = async () => {
    setIsValidating(true);
    
    // Clear previous markers
    if (monacoRef.current) {
      if (cEditorRef.current) monacoRef.current.editor.setModelMarkers(cEditorRef.current.getModel(), 'validator', []);
      if (fEditorRef.current) monacoRef.current.editor.setModelMarkers(fEditorRef.current.getModel(), 'validator', []);
    }

    try {
      const response = await axios.post('http://127.0.0.1:5000/api/validate', {
        c_code: cCode,
        fortran_code: fCode
      });
      
      const results = response.data.results;
      if (results && results.length > 0) {
        applyMarkers(results);
        setValidationErrors(results);
      } else {
        setValidationErrors([]);
      }
    } catch (error) {
      alert("Error: " + (error.response?.data?.error || error.message));
    } finally {
      setIsValidating(false);
    }
  };

  const applyMarkers = (results) => {
    const cMarkers = [];
    const fMarkers = [];
    const monaco = monacoRef.current;

    results.forEach(issue => {
      const severity = issue.level === 'ERROR' ? monaco.MarkerSeverity.Error : monaco.MarkerSeverity.Warning;
      const msg = issue.msg;
      const loc = issue.loc || "";

      // Try to parse C line number: "C: something:line"
      const cMatch = loc.match(/C: [^:]+:(\d+)/);
      if (cMatch) {
        let line = parseInt(cMatch[1]);
        if (line === 0) line = 1; // Fallback to line 1 if unknown
        cMarkers.push({
          startLineNumber: line,
          startColumn: 1,
          endLineNumber: line,
          endColumn: 100, // Highlight whole line
          message: msg,
          severity: severity
        });
      }

      // Try to parse Fortran line number
      const fMatch = loc.match(/Fortran line (\d+|\?)/);
      if (fMatch) {
        let line = parseInt(fMatch[1]);
        if (isNaN(line) || line === 0) line = 1;
        fMarkers.push({
          startLineNumber: line,
          startColumn: 1,
          endLineNumber: line,
          endColumn: 100,
          message: msg,
          severity: severity
        });
      }
    });

    if (cEditorRef.current) {
      monaco.editor.setModelMarkers(cEditorRef.current.getModel(), 'validator', cMarkers);
    }
    if (fEditorRef.current) {
      monaco.editor.setModelMarkers(fEditorRef.current.getModel(), 'validator', fMarkers);
    }
  };

  return (
    <div className="ide-tab">

      <div className="ide-toolbar">
        <button 
          className={`btn ${isValidating ? 'loading' : ''}`}
          onClick={handleValidate}
          disabled={isValidating}
        >
          {isValidating ? <span className="spinner">⟳</span> : <Play size={16} />}
          Validate Code
        </button>
      </div>
      <div className="editor-container">
        <div className="editor-pane">
          <div className="editor-header">C Header (*.h)</div>
          <Editor
            height="100%"
            defaultLanguage="c"
            theme="vs-dark"
            value={cCode}
            onChange={setCCode}
            onMount={(editor, monaco) => handleEditorDidMount(editor, monaco, 'c')}
            options={{ minimap: { enabled: false }, fontSize: 14 }}
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
            onMount={(editor, monaco) => handleEditorDidMount(editor, monaco, 'f')}
            options={{ minimap: { enabled: false }, fontSize: 14 }}
          />
        </div>
      </div>
      
      {validationErrors !== null && (
        <div className="leetcode-console">
          <div className="console-header">
            <span>Test Result</span>
            <button className="close-btn" onClick={() => setValidationErrors(null)}>✕</button>
          </div>
          <div className="console-content">
            {validationErrors.length === 0 ? (
              <h2 className="status-text accepted">Accepted</h2>
            ) : (
              <>
                <h2 className="status-text rejected">Wrong Answer</h2>
                <ul>
                  {validationErrors.map((err, idx) => (
                    <li key={idx}>
                      <strong>{err.level}:</strong> {err.msg} <span className="err-loc">({err.loc})</span>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
