import { useState, useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { Play, Plus, ListChecks, CheckCircle, XCircle, Beaker } from 'lucide-react';
import axios from 'axios';

export default function TestCasesTab() {
  const [testCases, setTestCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [cCode, setCCode] = useState('');
  const [fCode, setFCode] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newCaseName, setNewCaseName] = useState('');
  const [validationErrors, setValidationErrors] = useState(null);
  
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchResults, setBatchResults] = useState(null);
  
  const cEditorRef = useRef(null);
  const fEditorRef = useRef(null);
  const monacoRef = useRef(null);

  const fetchTestCases = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:5000/api/testcases');
      setTestCases(res.data.cases || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchTestCases();
  }, []);

  const handleSelectCase = async (name) => {
    setSelectedCase(name);
    setValidationErrors(null);
    clearMarkers();
    try {
      const res = await axios.get(`http://127.0.0.1:5000/api/testcases/${name}`);
      setCCode(res.data.c_code);
      setFCode(res.data.fortran_code);
    } catch (e) {
      console.error(e);
    }
  };

  const clearMarkers = () => {
    if (monacoRef.current) {
      if (cEditorRef.current) monacoRef.current.editor.setModelMarkers(cEditorRef.current.getModel(), 'validator', []);
      if (fEditorRef.current) monacoRef.current.editor.setModelMarkers(fEditorRef.current.getModel(), 'validator', []);
    }
  };

  const handleEditorDidMount = (editor, monaco, type) => {
    if (type === 'c') cEditorRef.current = editor;
    if (type === 'f') fEditorRef.current = editor;
    if (!monacoRef.current) monacoRef.current = monaco;
  };

  const handleValidate = async () => {
    if (!selectedCase) return;
    setIsValidating(true);
    clearMarkers();

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

      const cMatch = loc.match(/C: [^:]+:(\d+)/);
      if (cMatch) {
        let line = parseInt(cMatch[1]);
        if (line === 0) line = 1;
        cMarkers.push({
          startLineNumber: line, startColumn: 1, endLineNumber: line, endColumn: 100,
          message: msg, severity: severity
        });
      }

      const fMatch = loc.match(/Fortran line (\d+|\?)/);
      if (fMatch) {
        let line = parseInt(fMatch[1]);
        if (isNaN(line) || line === 0) line = 1;
        fMarkers.push({
          startLineNumber: line, startColumn: 1, endLineNumber: line, endColumn: 100,
          message: msg, severity: severity
        });
      }
    });

    if (cEditorRef.current) monaco.editor.setModelMarkers(cEditorRef.current.getModel(), 'validator', cMarkers);
    if (fEditorRef.current) monaco.editor.setModelMarkers(fEditorRef.current.getModel(), 'validator', fMarkers);
  };

  const handleRunAll = async () => {
    setBatchRunning(true);
    setBatchResults(null);
    try {
      const res = await axios.post('http://127.0.0.1:5000/api/testcases/run_all');
      setBatchResults(res.data.results);
    } catch (e) {
      alert("Error running batch tests.");
    } finally {
      setBatchRunning(false);
    }
  };

  const handleAddTest = async () => {
    if (!newCaseName.trim()) return;
    try {
      await axios.post(`http://127.0.0.1:5000/api/testcases/${newCaseName}`, {
        c_code: '// New C Header\n',
        fortran_code: '! New Fortran Code\n'
      });
      setShowAddModal(false);
      setNewCaseName('');
      fetchTestCases();
      handleSelectCase(newCaseName);
    } catch (e) {
      alert("Error adding test case.");
    }
  };

  return (
    <div className="test-cases-tab">
      <div className="sidebar">
        <div className="sidebar-header">
          <h3>Test Cases</h3>
          <div className="sidebar-actions">
            <button className="icon-btn" onClick={() => setShowAddModal(true)} title="Add Test Case">
              <Plus size={16} />
            </button>
            <button className="icon-btn" onClick={handleRunAll} disabled={batchRunning} title="Run All">
              {batchRunning ? <span className="spinner">⟳</span> : <ListChecks size={16} />}
            </button>
          </div>
        </div>
        <div className="case-list">
          {testCases.map(tc => (
            <div 
              key={tc} 
              className={`case-item ${selectedCase === tc ? 'active' : ''}`}
              onClick={() => handleSelectCase(tc)}
            >
              <Beaker size={14} className="case-icon" />
              <span>{tc}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="main-area">
        {batchResults && (
          <div className="batch-results-overlay">
            <div className="batch-results-header">
              <h3>Batch Run Results</h3>
              <button className="close-btn" onClick={() => setBatchResults(null)}>✕</button>
            </div>
            <div className="batch-results-list">
              {Object.entries(batchResults).map(([caseName, data]) => (
                <div key={caseName} className={`batch-result-item ${data.status}`}>
                  <span className="case-name">{caseName}</span>
                  <span className="case-status">
                    {data.status === 'accepted' ? <CheckCircle size={16} color="#10b981" /> : <XCircle size={16} color="#ef4444" />}
                    {data.issues > 0 ? ` (${data.issues} issues)` : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}



        {selectedCase ? (
          <>
            <div className="ide-toolbar">
              <div className="selected-case-title">Editing: {selectedCase}</div>
              <button 
                className={`btn ${isValidating ? 'loading' : ''}`}
                onClick={handleValidate}
                disabled={isValidating}
              >
                {isValidating ? <span className="spinner">⟳</span> : <Play size={16} />}
                Run Test Case
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
          </>
        ) : (
          <div className="empty-state">
            <Beaker size={48} className="empty-icon" />
            <h2>Select a Test Case</h2>
            <p>Choose a test case from the sidebar to view and validate it.</p>
          </div>
        )}
      </div>

      {showAddModal && (
        <div className="modal-backdrop">
          <div className="modal">
            <h3>Add New Test Case</h3>
            <input 
              type="text" 
              placeholder="Test case name (e.g. case_31)"
              value={newCaseName}
              onChange={e => setNewCaseName(e.target.value)}
              autoFocus
            />
            <div className="modal-actions">
              <button className="btn secondary" onClick={() => setShowAddModal(false)}>Cancel</button>
              <button className="btn" onClick={handleAddTest}>Create</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
