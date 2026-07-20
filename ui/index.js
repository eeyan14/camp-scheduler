let pyodideReadyPromise = null;

function setOutputContent(html) {
  const output = document.getElementById('output');

  if (!output) {
    return;
  }

  output.innerHTML = html;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function renderScheduleResult(result) {
  if (!result || !result.success) {
    return `<p>${escapeHtml(result?.message || 'No schedule data available.')}</p>`;
  }

  const activityNames = result.activities || [];
  const masterRows = (result.master_schedule || [])
    .map((row) => {
      const cells = [
        `<td>${escapeHtml(row.day)}</td>`,
        `<td>${escapeHtml(row.time)}</td>`,
      ];

      activityNames.forEach((activity) => {
        const groups = row.activities?.[activity] || [];
        const value = groups.length ? groups.join(', ') : '---';
        cells.push(`<td>${escapeHtml(value)}</td>`);
      });

      return `<tr>${cells.join('')}</tr>`;
    })
    .join('');

  const perGroupItems = Object.entries(result.per_group || {})
    .filter(([, events]) => events && events.length)
    .map(([group, events]) => {
      const dayGroups = {};
      events.forEach((event) => {
        if (!dayGroups[event.day]) {
          dayGroups[event.day] = [];
        }
        dayGroups[event.day].push(
          `<li>${escapeHtml(event.start_str)} - ${escapeHtml(event.end_str)} : ${escapeHtml(event.activity)}</li>`,
        );
      });

      const daySections = Object.entries(dayGroups)
        .map(
          ([day, items]) => `
          <div class="group-day-block">
            <div class="group-day-title">${escapeHtml(day)}</div>
            <ul class="group-day-list">${items.join('')}</ul>
          </div>
        `,
        )
        .join('');

      return `
        <div class="group-card">
          <div class="group-title">${escapeHtml(group)}</div>
          <div class="group-day-grid">${daySections}</div>
        </div>
      `;
    })
    .join('');

  const perActivityItems = Object.entries(result.per_activity || {})
    .filter(([, events]) => events && events.length)
    .map(([activity, events]) => {
      const dayGroups = {};
      events.forEach((event) => {
        if (!dayGroups[event.day]) {
          dayGroups[event.day] = [];
        }
        dayGroups[event.day].push(
          `<li>${escapeHtml(event.start_str)} - ${escapeHtml(event.end_str)} : ${escapeHtml(event.group)}</li>`,
        );
      });

      const daySections = Object.entries(dayGroups)
        .map(
          ([day, items]) => `
          <div class="group-day-block">
            <div class="group-day-title">${escapeHtml(day)}</div>
            <ul class="group-day-list">${items.join('')}</ul>
          </div>
        `,
        )
        .join('');

      return `
        <div class="group-card">
          <div class="group-title">${escapeHtml(activity)}</div>
          <div class="group-day-grid">${daySections}</div>
        </div>
      `;
    })
    .join('');

  return `
    <section class="schedule-section">
      <h3>Aggregate Schedule</h3>
      <table class="schedule-table">
        <thead>
          <tr>
            <th>Day</th>
            <th>Time</th>
            ${activityNames.map((activity) => `<th>${escapeHtml(activity)}</th>`).join('')}
          </tr>
        </thead>
        <tbody>${masterRows}</tbody>
      </table>
    </section>

    <section class="schedule-section">
      <h3>Per Group</h3>
      <div class="group-grid">${perGroupItems || '<div class="muted">No groups scheduled.</div>'}</div>
    </section>

    <section class="schedule-section">
      <h3>Per Activity</h3>
      <div class="group-grid">${perActivityItems || '<div class="muted">No activities scheduled.</div>'}</div>
    </section>
  `;
}

// Called from Python via `from js import window; window.pyodideWrite(...)`
window.pyodideWrite = function (msg) {
  try {
    setOutputContent(`<p>${escapeHtml(msg)}</p>`);
  } catch (e) {
    // ignore
  }
};

async function initPyodide() {
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
      fetch('../main.py'),
      fetch('../schedule_utils.py'),
      fetch('../solver.py'),
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
  } catch (err) {
    setOutputContent(`<p>${escapeHtml(String(err))}</p>`);
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
