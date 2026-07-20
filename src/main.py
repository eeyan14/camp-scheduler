import os
from datetime import datetime, timedelta

import numpy as np
import schedule_utils
from solver import solver


# ==========================================
# 1. SETUP PARAMETERS (With Comprehensive Examples)
# ==========================================
# Jagged blocks: Each day has its own distinct sequence of 15-minute intervals
# All times are in 24-hour format for clarity
# Mon PM: 2-6pm (14:00-18:00), Tue AM: 10-11am (10:00-11:00), etc.
day_blocks = {
    "Mon PM": [
        "14:00",
        "14:15",
        "14:30",
        "14:45",
        "15:00",
        "15:15",
        "15:30",
        "15:45",
        "16:00",
        "16:15",
        "16:30",
        "16:45",
        "17:00",
        "17:15",
        "17:30",
        "17:45",
    ],
    "Tue AM": ["10:00", "10:15", "10:30", "10:45"],
    "Tue Lunch": ["12:30", "12:45", "13:00"],
    "Tue PM": ["16:00", "16:15", "16:30", "16:45", "17:00", "17:15", "17:30", "17:45"],
    "Wed AM": ["10:00", "10:15", "10:30", "10:45"],
    "Wed Lunch": ["12:30", "12:45"],
    "Wed PM": ["16:00", "16:15", "16:30", "16:45"],
    "Thu AM": ["10:00", "10:15", "10:30", "10:45"],
    "Thu PM": ["16:00", "16:15", "16:30", "16:45", "17:00", "17:15", "17:30", "17:45"],
}

boys_group_ages = {
    "B:A/J": 7,
    "B:N/T": 8,
    "B:J/J": 9,
    "B:B/A": 10,
    "B:S/S": 10,
    "B:S/W": 12,
    "B:D/J": 12,
}

girls_group_ages = {
    "G:A/A": 6,
    "G:E/B": 8,
    "G:S/Z": 10,
    "G:H/A": 11,
    "G:A/K": 12,
    "G:J/R": 12,
}

# duration: measured in units of 15-minute blocks, e.g. 2 = 30 minutes
# max_groups: capacity caps (max simultaneous cohorts)
# gender_policy: one of: "Any", "Boys Only", "Girls Only"
# age_range: array of [min, max] inclusive
# schedule: availability of activity for sessions
# (optional) gap: cooldown period in between consecutive sessions of the same activity
# (optional) allowed_start_minutes: array of minute start times allowed for activity, e.g. [0, 30] = activity can start at XX:00 and XX:30
activities_list = [
    {
        "name": "Archery",
        "duration": 3,
        "max_groups": 2,
        "gender_policy": "Any",
        "age_range": [6, 12],
        "schedule": ["Mon PM", "Tue AM", "Tue PM"],
    },
    {
        "name": "Biking",
        "duration": 3,
        "max_groups": 2,  # can be 3 if needed
        "gender_policy": "Any",
        "age_range": [6, 12],
        "schedule": [
            "Mon PM",
            "Tue AM",
            "Tue PM",
            "Wed AM",
            "Wed PM",
            "Thu AM",
            "Thu PM",
        ],
    },
    {
        "name": "Climbing (<10)",
        "duration": 3,
        "max_groups": 2,
        "gender_policy": "Any",
        "age_range": [6, 10],
        "schedule": ["Mon PM", "Tue AM", "Tue PM"],
    },
    {
        "name": "Climbing (Grads)",
        "duration": 4,
        "max_groups": 10,  # big number to accomodate all grad groups
        "gender_policy": "Any",
        "age_range": [11, 12],
        "schedule": ["Tue AM"],
    },
    {
        "name": "Horses",
        "duration": 2,
        "max_groups": 1,
        "gender_policy": "Any",
        "age_range": [6, 12],
        "schedule": ["Mon PM", "Tue AM", "Tue PM", "Wed AM", "Wed PM"],
    },
    {
        "name": "Portraits",
        "duration": 1,
        "max_groups": 1,
        "gender_policy": "Any",
        "age_range": [6, 12],
        "schedule": ["Tue AM", "Tue Lunch", "Wed AM", "Wed Lunch"],
    },
    {
        "name": "Tea Party",
        "duration": 4,
        "max_groups": 1,
        "gender_policy": "Girls Only",
        "age_range": [6, 12],
        "schedule": ["Tue AM", "Tue PM", "Wed AM", "Wed PM", "Thu AM", "Thu PM"],
        "gap": 4,  # 1 hour gap
        "allowed_start_minutes": [0],  # only start at the top of the hour
    },
]

# Travel Overhead Grid (Measured in 15-minute time-blocks)
# Rows/Cols map sequentially to:
# Index 0 = Archery
#       1 = Biking
#       2 = Climbing
#       3 = Climbing (Grads)
#       ...
travel_matrix = np.array(
    [
        [0, 1, 1, 1, 1, 1, 1],  # From Archery
        [1, 0, 1, 1, 1, 1, 1],  # From Biking
        [1, 1, 0, 1, 1, 1, 1],  # From Climbing (<10)
        [1, 1, 1, 0, 1, 1, 1],  # From Climbing (Grads)
        [1, 1, 1, 1, 0, 1, 1],  # From Horses
        [1, 1, 1, 1, 1, 0, 1],  # From Portraits
        [1, 1, 1, 1, 1, 1, 0],  # From Tea Party
    ]
)


def main(output="file"):
    if output not in {"file", "ui"}:
        raise ValueError("output must be either 'file' or 'ui'")

    res, inputs = solver(
        day_blocks, boys_group_ages, girls_group_ages, activities_list, travel_matrix
    )

    if not res.success:
        return {"success": False, "mode": output, "message": res.message}

    sol = res.x
    (
        num_groups,
        num_activities,
        activity_durations,
        activities,
        days,
        get_var_idx,
        groups,
    ) = inputs.values()

    # Extract all scheduled events
    events = []
    for g in range(num_groups):
        for a in range(num_activities):
            dur = activity_durations[activities[a]]
            for d in days:
                num_slots = len(day_blocks[d])
                for t in range(num_slots):
                    if sol[get_var_idx(g, a, d, t)] > 0.5:
                        start_time = datetime.strptime(day_blocks[d][t], "%H:%M")
                        end_time = start_time + timedelta(minutes=15 * dur)
                        events.append(
                            {
                                "group": groups[g],
                                "activity": activities[a],
                                "day": d,
                                "start_str": start_time.strftime("%I:%M %p"),
                                "end_str": end_time.strftime("%I:%M %p"),
                                "day_idx": days.index(d),
                                "time_idx": t,
                            }
                        )

    if output == "file":
        schedule_utils.write_master_schedule_to_file(
            events, days, day_blocks, activities
        )
        schedule_utils.write_per_group_schedule_to_file(events, groups)
        schedule_utils.write_per_activity_schedule_to_file(events, activities)
        print(f"Schedules successfully written to {os.getcwd()}")
        return {
            "success": True,
            "mode": "file",
            "message": f"Schedules successfully written to {os.getcwd()}",
        }

    return {
        "success": True,
        "mode": "ui",
        **schedule_utils.build_schedule_payload(
            events, days, day_blocks, activities, groups
        ),
    }


if __name__ == "__main__":
    main(output="file")
