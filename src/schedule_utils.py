from datetime import datetime


def write_master_schedule_to_file(
    events, days, day_blocks, activities, filename="schedule_matrix.md"
):
    """Write schedule for all groups and activities as a table to a markdown file."""
    with open(filename, "w") as f:
        # Create header
        header = "| Day | Time | " + " | ".join(activities) + " |"
        f.write(header + "\n")

        # Create separator
        separator = "|---|---|-" + "-|-".join(["---"] * len(activities)) + "-|"
        f.write(separator + "\n")

        # Fill rows
        for d in days:
            for t, time_str in enumerate(day_blocks[d]):
                row_data = [d, time_str]

                # Check for scheduled activities in this time block
                for a in activities:
                    active_groups = []
                    for e in events:
                        if e["day"] == d and e["activity"] == a:
                            e_start = datetime.strptime(e["start_str"], "%I:%M %p")
                            e_end = datetime.strptime(e["end_str"], "%I:%M %p")
                            t_current = datetime.strptime(time_str, "%H:%M")

                            if e_start <= t_current < e_end:
                                active_groups.append(e["group"])

                    row_data.append(
                        ", ".join(active_groups) if active_groups else "---"
                    )

                # Write the row
                f.write("| " + " | ".join(row_data) + " |\n")


def write_per_group_schedule_to_file(events, groups):
    """Write per-group schedules to a text file."""
    with open("schedule_by_group.txt", "w") as f2:
        f2.write("Camp Schedule - By Group:\n\n")
        for g_name in groups:
            f2.write(f"==================== {g_name.upper()} ====================\n")
            g_events = [e for e in events if e["group"] == g_name]
            g_events.sort(key=lambda x: (x["day_idx"], x["time_idx"]))

            if not g_events:
                f2.write("  No activities scheduled.\n")
            else:
                current_day = ""
                for e in g_events:
                    if e["day"] != current_day:
                        f2.write(f"\n  --- {e['day']} ---\n")
                        current_day = e["day"]
                    f2.write(
                        f"    {e['start_str']} - {e['end_str']} : {e['activity']}\n"
                    )
            f2.write("\n")


def write_per_activity_schedule_to_file(events, activities):
    """Write per-activity schedules to a text file."""
    with open("schedule_by_activity.txt", "w") as f3:
        f3.write("Camp Schedule - By Activity:\n\n")
        for a_name in activities:
            f3.write(f"==================== {a_name.upper()} ====================\n")
            a_events = [e for e in events if e["activity"] == a_name]
            a_events.sort(key=lambda x: (x["day_idx"], x["time_idx"]))

            if not a_events:
                f3.write("  No groups scheduled.\n")
            else:
                current_day = ""
                for e in a_events:
                    if e["day"] != current_day:
                        f3.write(f"\n  --- {e['day']} ---\n")
                        current_day = e["day"]
                    f3.write(f"    {e['start_str']} - {e['end_str']} : {e['group']}\n")
            f3.write("\n")


def build_schedule_payload(events, days, day_blocks, activities, groups):
    """Parse schedule content into a format usable for printing to the UI."""
    master_schedule = []
    for d in days:
        for t, time_str in enumerate(day_blocks[d]):
            row = {"day": d, "time": time_str, "activities": {}}
            for activity_name in activities:
                active_groups = []
                for event in events:
                    if event["day"] != d or event["activity"] != activity_name:
                        continue

                    event_start = datetime.strptime(event["start_str"], "%I:%M %p")
                    event_end = datetime.strptime(event["end_str"], "%I:%M %p")
                    current_time = datetime.strptime(time_str, "%H:%M")

                    if event_start <= current_time < event_end:
                        active_groups.append(event["group"])

                row["activities"][activity_name] = active_groups
            master_schedule.append(row)

    per_group = {}
    for group_name in groups:
        group_events = [event for event in events if event["group"] == group_name]
        group_events.sort(key=lambda item: (item["day_idx"], item["time_idx"]))
        per_group[group_name] = group_events

    per_activity = {}
    for activity_name in activities:
        activity_events = [
            event for event in events if event["activity"] == activity_name
        ]
        activity_events.sort(key=lambda item: (item["day_idx"], item["time_idx"]))
        per_activity[activity_name] = activity_events

    return {
        "master_schedule": master_schedule,
        "per_group": per_group,
        "per_activity": per_activity,
        "events": events,
        "days": days,
        "day_blocks": day_blocks,
        "activities": activities,
        "groups": groups,
    }
