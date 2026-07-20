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
          `<div class="item">${escapeHtml(event.start_str)} - ${escapeHtml(event.end_str)} : ${escapeHtml(event.activity)}</div>`,
        );
      });

      const daySections = Object.entries(dayGroups)
        .map(
          ([day, items], index) => `
          <div class="day-section">
            <div class="ui tiny header">${escapeHtml(day)}</div>
            <div class="ui relaxed list">${items.join('')}</div>
            ${index < Object.keys(dayGroups).length - 1 ? '<div class="ui divider"></div>' : ''}
          </div>
        `,
        )
        .join('');

      return `
        <div class="ui card fluid">
          <div class="content">
            <div class="header">${escapeHtml(group)}</div>
          </div>
          <div class="content">${daySections}</div>
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
          `<div class="item">${escapeHtml(event.start_str)} - ${escapeHtml(event.end_str)} : ${escapeHtml(event.group)}</div>`,
        );
      });

      const daySections = Object.entries(dayGroups)
        .map(
          ([day, items], index) => `
          <div class="day-section">
            <div class="ui tiny header">${escapeHtml(day)}</div>
            <div class="ui relaxed list">${items.join('')}</div>
            ${index < Object.keys(dayGroups).length - 1 ? '<div class="ui divider"></div>' : ''}
          </div>
        `,
        )
        .join('');

      return `
        <div class="ui card fluid">
          <div class="content">
            <div class="header">${escapeHtml(activity)}</div>
          </div>
          <div class="content">${daySections}</div>
        </div>
      `;
    })
    .join('');

  return `
    <section class="schedule-section">
      <h3 class="ui header">Aggregate Schedule</h3>
      <table class="ui celled striped table unstackable">
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
      <h3 class="ui header">Per Group</h3>
      <div class="group-grid">${perGroupItems || '<div class="ui message">No groups scheduled.</div>'}</div>
    </section>

    <section class="schedule-section">
      <h3 class="ui header">Per Activity</h3>
      <div class="group-grid">${perActivityItems || '<div class="ui message">No activities scheduled.</div>'}</div>
    </section>
  `;
}
