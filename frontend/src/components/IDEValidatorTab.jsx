import { useState, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { Play, Terminal, Copy } from 'lucide-react';
import axios from 'axios';

const DEFAULT_C = `void do_math(int rows, int cols, double *matrix);\n`;

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

  const [cliOutput, setCliOutput] = useState(null);
  const [cliCommand, setCliCommand] = useState('python fc_validator.py --fortran input.f90 --c input.h');
  const [isCliRunning, setIsCliRunning] = useState(false);
  const [consoleTab, setConsoleTab] = useState('validation');
  const [copied, setCopied] = useState(false);

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
    setConsoleTab('validation');

    if (monacoRef.current) {
      if (cEditorRef.current) monacoRef.current.editor.setModelMarkers(cEditorRef.current.getModel(), 'validator', []);
      if (fEditorRef.current) monacoRef.current.editor.setModelMarkers(fEditorRef.current.getModel(), 'validator', []);
    }

    try {
      const response = await axios.post('http://127.0.0.1:5000/api/validate', {
        c_code: cCode,
        fortran_code: fCode
      });
      const results = response.data.results || [];
      if (results.length > 0) applyMarkers(results);
      setValidationErrors(results);
    } catch (error) {
      const errMsg = error.response?.data?.error
        ? `Backend error: ${error.response.data.error}`
        : `Cannot reach backend (is server.py running?): ${error.message}`;
      setValidationErrors([{ level: 'ERROR', msg: errMsg, loc: 'Network' }]);
    } finally {
      setIsValidating(false);
    }
  };

  const handleRunCli = async () => {
    setIsCliRunning(true);
    setConsoleTab('cli');
    try {
      const response = await axios.post('http://127.0.0.1:5000/api/cli-run', {
        c_code: cCode,
        fortran_code: fCode,
        case_name: 'custom_run'
      });
      setCliCommand(response.data.command);
      setCliOutput(response.data.output);
    } catch (error) {
      setCliOutput('Error running CLI: ' + (error.response?.data?.error || error.message));
    } finally {
      setIsCliRunning(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(cliCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const applyMarkers = (results) => {
    if (!monacoRef.current) return;
    const cMarkers = [];
    const fMarkers = [];
    const monaco = monacoRef.current;

    results.forEach(issue => {
      const severity = issue.level === 'ERROR' ? monaco.MarkerSeverity.Error : monaco.MarkerSeverity.Warning;
      const msg = issue.msg;
      const loc = issue.loc || '';

      const cMatch = loc.match(/C:.*:(\d+)/);
      if (cMatch) {
        let line = parseInt(cMatch[1]);
        if (line === 0) line = 1;
        cMarkers.push({ startLineNumber: line, startColumn: 1, endLineNumber: line, endColumn: 100, message: msg, severity });
      }

      const fMatch = loc.match(/Fortran line (\d+|\?)/);
      if (fMatch) {
        let line = parseInt(fMatch[1]);
        if (isNaN(line) || line === 0) line = 1;
        fMarkers.push({ startLineNumber: line, startColumn: 1, endLineNumber: line, endColumn: 100, message: msg, severity });
      }
    });

    if (cEditorRef.current) monaco.editor.setModelMarkers(cEditorRef.current.getModel(), 'validator', cMarkers);
    if (fEditorRef.current) monaco.editor.setModelMarkers(fEditorRef.current.getModel(), 'validator', fMarkers);
  };

  return (
    <div className="ide-tab">

      {/* Toolbar */}
      <div className="ide-toolbar">
        <button
          className={`btn secondary ${isCliRunning ? 'loading' : ''}`}
          onClick={handleRunCli}
          disabled={isCliRunning}
          style={{ marginRight: '0.5rem' }}
        >
          {isCliRunning ? <span className="spinner">⟳</span> : <Terminal size={16} />}
          Run CLI Command
        </button>
        <button
          className={`btn ${isValidating ? 'loading' : ''}`}
          onClick={handleValidate}
          disabled={isValidating}
        >
          {isValidating ? <span className="spinner">⟳</span> : <Play size={16} />}
          Validate Code
        </button>
      </div>

      {/* Editors */}
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

      {/* Console Panel */}
      <div className="leetcode-console">
        <div className="console-header-tabs" style={{ display: 'flex', borderBottom: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.1)' }}>
          <button
            className={`console-tab-btn ${consoleTab === 'validation' ? 'active' : ''}`}
            onClick={() => setConsoleTab('validation')}
          >
            Validation Report
          </button>
          <button
            className={`console-tab-btn ${consoleTab === 'cli' ? 'active' : ''}`}
            onClick={() => setConsoleTab('cli')}
          >
            CLI Terminal
          </button>
          <button
            className="close-btn"
            style={{ marginLeft: 'auto', marginRight: '1rem', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}
            onClick={() => { setValidationErrors(null); setCliOutput(null); setConsoleTab('validation'); }}
          >
            ✕
          </button>
        </div>

        <div className="console-content" style={{ overflowY: 'auto', flex: 1, padding: '1rem' }}>
          {consoleTab === 'validation' ? (
            validationErrors !== null ? (
              validationErrors.length === 0 ? (
                <h2 className="status-text accepted">✓ All checks passed — interfaces are compatible.</h2>
              ) : (
                <>
                  <h2 className="status-text rejected">✗ {validationErrors.length} issue{validationErrors.length > 1 ? 's' : ''} found</h2>
                  <ul>
                    {validationErrors.map((err, idx) => (
                      <li key={idx}>
                        <strong>{err.level}:</strong> {err.msg} <span className="err-loc">({err.loc})</span>
                      </li>
                    ))}
                  </ul>
                </>
              )
            ) : (
              <h3 className="status-text neutral">Select a test case or paste code, then click "Validate Code".</h3>
            )
          ) : (
            <div className="cli-terminal-container">
              <div className="cli-command-line">
                <span className="prompt">$</span> {cliCommand}
                <button className="copy-cmd-btn" onClick={copyToClipboard}>
                  {copied ? 'Copied!' : <><Copy size={12} /> Copy</>}
                </button>
              </div>
              <div className="cli-terminal-output">
                {isCliRunning ? (
                  <div className="terminal-loading"><span className="spinner">⟳</span> Executing python fc_validator.py...</div>
                ) : (
                  <pre>{cliOutput || "Click 'Run CLI Command' to see direct compiler AST-dump CLI validation report output."}</pre>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
