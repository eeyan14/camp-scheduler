import { escapeHtml, renderScheduleResult, setOutputContent, } from './renderUtils.js';
import { initPyodide } from './pyodideUtils.js';
let pyodideReadyPromise = null;
window.pyodideWrite = function (msg) {
    try {
        setOutputContent(`<p>${escapeHtml(msg)}</p>`);
    }
    catch {
        // ignore
    }
};
async function evaluatePython() {
    if (!pyodideReadyPromise) {
        return;
    }
    const pyodide = await pyodideReadyPromise;
    const runBtn = document.getElementById('runBtn');
    if (runBtn) {
        runBtn.disabled = true;
        runBtn.textContent = 'Running...';
    }
    try {
        const [mainResponse, utilsResponse, solverResponse] = await Promise.all([
            fetch('./src/main.py'),
            fetch('./src/schedule_utils.py'),
            fetch('./src/solver.py'),
        ]);
        if (!mainResponse.ok || !utilsResponse.ok || !solverResponse.ok) {
            throw new Error('Could not load Python file(s)');
        }
        const mainSource = await mainResponse.text();
        const utilsSource = await utilsResponse.text();
        const solverSource = await solverResponse.text();
        pyodide.FS.mkdirTree('/tmp');
        pyodide.FS.writeFile('/tmp/main.py', mainSource);
        pyodide.FS.writeFile('/tmp/schedule_utils.py', utilsSource);
        pyodide.FS.writeFile('/tmp/solver.py', solverSource);
        await pyodide.loadPackage(['numpy', 'scipy']);
        const result = await pyodide.runPythonAsync(`
  import sys
  from js import window
  class _Writer:
    def write(self, s):
      if s:
        try:
          window.pyodideWrite(str(s))
        except Exception:
          pass
    def flush(self):
      pass
  sys.stdout = _Writer()
  sys.stderr = _Writer()
  sys.path.insert(0, '/tmp')
  import main
  main.main(output='ui')
  `);
        setOutputContent(renderScheduleResult(result));
    }
    catch (err) {
        setOutputContent(`<p>${escapeHtml(String(err))}</p>`);
    }
    finally {
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.textContent = 'Run';
        }
    }
}
window.evaluatePython = evaluatePython;
document.addEventListener('DOMContentLoaded', () => {
    pyodideReadyPromise = initPyodide();
});
//# sourceMappingURL=index.js.map