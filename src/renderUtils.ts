export function setOutputContent(html: string): void {
  const output = document.getElementById('output');

  if (!output) {
    return;
  }

  output.innerHTML = html;
}

export function escapeHtml(value: unknown): string {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

export function renderScheduleResult(result: any): string {
  if (!result || !result.success) {
    return `<p>${escapeHtml(result?.message || 'No schedule data available.')}</p>`;
  }

  const activityNames = result.activities || [];
  const masterRows = (result.master_schedule || [])
    .map((row: any) => {
      const cells = [
        `<td>${escapeHtml(row.day)}</td>`,
        `<td>${escapeHtml(row.time)}</td>`,
      ];

      activityNames.forEach((activity: string) => {
        const groups = row.activities?.[activity] || [];
        const value = groups.length ? groups.join(', ') : '---';
        cells.push(`<td>${escapeHtml(value)}</td>`);
      });

      return `<tr>${cells.join('')}</tr>`;
    })
    .join('');

  const perGroupItems = Object.entries(result.per_group || {})
    .filter(([, events]) => events && (events as any[]).length)
    .map(([group, events]) => {
      const dayGroups: Record<string, string[]> = {};
      (events as any[]).forEach((event) => {
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
    .filter(([, events]) => events && (events as any[]).length)
    .map(([activity, events]) => {
      const dayGroups: Record<string, string[]> = {};
      (events as any[]).forEach((event) => {
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
            ${activityNames.map((activity: string) => `<th>${escapeHtml(activity)}</th>`).join('')}
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
