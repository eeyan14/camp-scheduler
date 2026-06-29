let pyodideReadyPromise = null;

function addToOutput(message) {
  const output = document.getElementById('output');

  if (!output) {
    return;
  }
}

async function initPyodide() {
  const output = document.getElementById('output');

  if (output) {
    output.value = 'Initializing...\n';
  }

  const pyodide = await globalThis.loadPyodide();

  if (output) {
    output.value += 'Ready!\n';
  }

  return pyodide;
}

async function evaluatePython() {
  if (!pyodideReadyPromise) {
    return;
  }

  const pyodide = await pyodideReadyPromise;

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
sys.path.insert(0, '/tmp')
import main
`);

    addToOutput('Executed main.py');
  } catch (err) {
    addToOutput(String(err));
  }
}

window.evaluatePython = evaluatePython;

document.addEventListener('DOMContentLoaded', () => {
  pyodideReadyPromise = initPyodide();
});
