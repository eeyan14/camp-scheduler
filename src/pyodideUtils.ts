export async function initPyodide(): Promise<any> {
  const runBtn = document.getElementById('runBtn') as HTMLButtonElement | null;

  if (runBtn) {
    runBtn.disabled = true;
    runBtn.textContent = 'Loading script...';
  }

  const pyodide = await (globalThis as any).loadPyodide();

  if (runBtn) {
    runBtn.disabled = false;
    runBtn.textContent = 'Generate schedule';
  }

  return pyodide;
}
