from datetime import datetime


def generate_markdown_schedule(
    events, days, day_blocks, activities, filename="schedule_matrix.md"
):
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

    print(f"Markdown schedule saved to {filename}")
