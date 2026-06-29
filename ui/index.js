let pyodideReadyPromise = null;

function addToOutput(message) {
  const output = document.getElementById('output');

  if (!output) {
    return;
  }

  output.value += message + '\n';
}

// Called from Python via `from js import window; window.pyodideWrite(...)`
window.pyodideWrite = function (msg) {
  try {
    addToOutput(msg);
  } catch (e) {
    // ignore
  }
};

async function initPyodide() {
  const runBtn = document.getElementById('runBtn');

  if (runBtn) {
    runBtn.disabled = true;
    runBtn.textContent = 'Loading...';
  }

  const pyodide = await globalThis.loadPyodide();

  if (runBtn) {
    runBtn.disabled = false;
    runBtn.textContent = 'Generate schedule';
  }

  return pyodide;
}

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
    addToOutput('Loading main.py...');

    const [mainResponse, utilsResponse] = await Promise.all([
      fetch('../main.py'),
      fetch('../schedule_utils.py'),
    ]);

    if (!mainResponse.ok || !utilsResponse.ok) {
      throw new Error('Could not load main.py or schedule_utils.py');
    }

    const mainSource = await mainResponse.text();
    const utilsSource = await utilsResponse.text();

    pyodide.FS.mkdirTree('/tmp');
    pyodide.FS.writeFile('/tmp/main.py', mainSource);
    pyodide.FS.writeFile('/tmp/schedule_utils.py', utilsSource);

    await pyodide.loadPackage(['numpy', 'scipy']);

    await pyodide.runPythonAsync(`
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
  `);

    addToOutput('Executed main.py');
  } catch (err) {
    addToOutput(String(err));
  } finally {
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
