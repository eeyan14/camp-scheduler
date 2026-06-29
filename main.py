import numpy as np
import os
import schedule_utils
from solver import solver
from datetime import datetime, timedelta
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import csr_matrix

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

# ==========================================
# 2-4. SOLVER EXECUTION
# ==========================================
# Pass the inputs to the solver
res, inputs = solver(day_blocks, boys_group_ages, girls_group_ages, activities_list, travel_matrix)

# ==========================================
# 5. USER-FRIENDLY STRING FORMATTED OUTPUT
# ==========================================


if res.success:
    print("Camp Schedule Found. Generating files...\n")
    sol = res.x
    num_groups, num_activities, activity_durations, activities, days, get_var_idx, groups = inputs.values()

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

    # ---------------------------------------------------------
    # 1. FILE: CURRENT PRINTED CONTENT (By Time)
    # ---------------------------------------------------------
    schedule_utils.generate_markdown_schedule(events, days, day_blocks, activities)

    # ---------------------------------------------------------
    # 2. FILE: PER-GROUP SCHEDULE
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # 3. FILE: PER-ACTIVITY SCHEDULE
    # ---------------------------------------------------------
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

    print(f"Schedules successfully written to {os.getcwd()}")
else:
    print("Optimization failed to find a valid solution:", res.message)
