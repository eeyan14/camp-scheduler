export async function initPyodide() {
    const runBtn = document.getElementById('runBtn');
    if (runBtn) {
        runBtn.disabled = true;
        runBtn.textContent = 'Loading script...';
    }
    const pyodide = await globalThis.loadPyodide();
    if (runBtn) {
        runBtn.disabled = false;
        runBtn.textContent = 'Generate schedule';
    }
    return pyodide;
}
//# sourceMappingURL=pyodideUtils.js.map