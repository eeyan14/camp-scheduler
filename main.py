import numpy as np
import os
import schedule_utils
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

days = list(day_blocks.keys())

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

groups = list(boys_group_ages.keys()) + list(girls_group_ages.keys())

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

activities = list(map(lambda x: x["name"], activities_list))

num_groups = len(groups)
num_activities = len(activities)

# Calculate dynamic matrix offsets for jagged timelines
day_offsets = {}
total_time_blocks = 0
for d in days:
    day_offsets[d] = total_time_blocks
    total_time_blocks += len(day_blocks[d])

# Total number of binary decision variables in our 1D array space
num_vars = num_groups * num_activities * total_time_blocks

# Group Demographics
group_genders = {
    **{name: "Boys" for name in boys_group_ages},
    **{name: "Girls" for name in girls_group_ages},
}
group_ages = {**boys_group_ages, **girls_group_ages}

# split large object into smaller objects for use
activity_durations = {a["name"]: a["duration"] for a in activities_list}
activity_group_limits = {a["name"]: a["max_groups"] for a in activities_list}
activity_gender_rules = {a["name"]: a["gender_policy"] for a in activities_list}
activity_age_rules = {a["name"]: a["age_range"] for a in activities_list}
activity_availability = {a["name"]: a["schedule"] for a in activities_list}

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


# 4D Positional Flattening Helper Function
def get_var_idx(g, a, d_name, t_idx):
    global_t_idx = day_offsets[d_name] + t_idx
    return (
        (g * num_activities * total_time_blocks)
        + (a * total_time_blocks)
        + global_t_idx
    )


# ==========================================
# 2. OBJECTIVE FUNCTION & STATIC PRE-FILTERING
# ==========================================
# SciPy minimizes, so a negative coefficient forces maximization of activity placements.
c = -np.ones(num_vars)
integrality = np.ones(
    num_vars
)  # Force all decision outcomes to be strictly binary (0 or 1)

lower_bounds = np.zeros(num_vars)
upper_bounds = np.ones(num_vars)

# PRE-FILTER MATRIX TRUNCATION: Systematically clip out mathematically impossible variables
for g in range(num_groups):
    g_gender = group_genders[groups[g]]
    g_age = group_ages[groups[g]]

    for a in range(num_activities):
        act_name = activities[a]
        act_gender = activity_gender_rules[act_name]
        min_age, max_age = activity_age_rules[act_name]
        allowed_days = activity_availability[act_name]
        dur = activity_durations[act_name]

        # Validate profile combinations
        gender_conflict = act_gender != "Any" and act_gender != f"{g_gender} Only"
        age_conflict = g_age < min_age or g_age > max_age

        for d in days:
            day_conflict = d not in allowed_days
            num_slots = len(day_blocks[d])

            # If any policy boundary fails, permanently kill the entire timeline path
            if gender_conflict or age_conflict or day_conflict:
                for t in range(num_slots):
                    upper_bounds[get_var_idx(g, a, d, t)] = 0
            else:
                # CRITICAL FIX: Kill trailing time slots where the activity
                # would run past the end of the day block.
                for t in range(num_slots - dur + 1, num_slots):
                    upper_bounds[get_var_idx(g, a, d, t)] = 0

bounds = Bounds(lower_bounds, upper_bounds)
constraints = []

# ==========================================
# 3. CONSTRAINT GENERATION ENGINES (OPTIMIZED FOR SPARSE MEMORY)
# ==========================================

# Lists to build our Sparse Matrix coordinates
A_rows = []
A_cols = []
A_vals = []
lb_list = []
ub_list = []
current_row = 0


def add_constraint(row_dict, lb, ub):
    """Helper to convert a dictionary of active variables into sparse matrix coordinates"""
    global current_row
    if not row_dict:
        return
    for var_idx, val in row_dict.items():
        A_rows.append(current_row)
        A_cols.append(var_idx)
        A_vals.append(val)
    lb_list.append(lb)
    ub_list.append(ub)
    current_row += 1


# A. Uniqueness Rule: Each cohort must visit each eligible station exactly once
for g in range(num_groups):
    g_gender = group_genders[groups[g]]
    g_age = group_ages[groups[g]]
    for a in range(num_activities):
        act_name = activities[a]
        act_gender = activity_gender_rules[act_name]
        min_age, max_age = activity_age_rules[act_name]
        allowed_days = activity_availability[act_name]

        gender_conflict = act_gender != "Any" and act_gender != f"{g_gender} Only"
        age_conflict = g_age < min_age or g_age > max_age
        if gender_conflict or age_conflict:
            continue

        row_dict = {}
        for d in allowed_days:
            dur = activity_durations[act_name]
            num_slots = len(day_blocks[d])
            for t in range(num_slots - dur + 1):
                row_dict[get_var_idx(g, a, d, t)] = 1
        add_constraint(row_dict, 1, 1)

# B. Activity must fit in available time blocks
# (This remains managed by upper_bounds in Section 2, no linear constraints needed)

# C. Station Capacity: Enforce asset caps across ongoing sessions
for a in range(num_activities):
    dur = activity_durations[activities[a]]
    max_grps = activity_group_limits[activities[a]]

    for d in days:
        num_slots = len(day_blocks[d])
        for t in range(num_slots):
            row_dict = {}
            for g in range(num_groups):
                for t_start in range(max(0, t - dur + 1), t + 1):
                    row_dict[get_var_idx(g, a, d, t_start)] = 1
            add_constraint(row_dict, 0, max_grps)

# D. Cohort Integrity & Transit Lockouts
for g in range(num_groups):
    for d in days:
        num_slots = len(day_blocks[d])
        for t1 in range(num_slots):
            for a1 in range(num_activities):
                dur_a1 = activity_durations[activities[a1]]

                for a2 in range(num_activities):
                    travel_time = travel_matrix[a1, a2]
                    ready_at_block = t1 + dur_a1 + travel_time

                    for t2 in range(t1, min(num_slots, ready_at_block)):
                        if a1 == a2 and t1 == t2:
                            continue
                        row_dict = {
                            get_var_idx(g, a1, d, t1): 1,
                            get_var_idx(g, a2, d, t2): 1,
                        }
                        add_constraint(row_dict, 0, 1)

# E. Dynamic Gender Separation Loops (Left commented as in your original file, but optimized)
# for a in range(num_activities):
#     if activity_gender_rules[activities[a]] == "Any":
#         dur = activity_durations[activities[a]]
#         for d in days:
#             num_slots = len(day_blocks[d])
#             for t in range(num_slots):
#                 for g1 in range(num_groups):
#                     for g2 in range(g1 + 1, num_groups):
#                         if group_genders[groups[g1]] != group_genders[groups[g2]]:
#                             row_dict = {}
#                             for t_start1 in range(max(0, t - dur + 1), t + 1):
#                                 row_dict[get_var_idx(g1, a, d, t_start1)] = 1
#                             for t_start2 in range(max(0, t - dur + 1), t + 1):
#                                 row_dict[get_var_idx(g2, a, d, t_start2)] = 1
#                             add_constraint(row_dict, 0, 1)

# F. Synchronized Batch Starts (No Staggered Starts)
for a in range(num_activities):
    dur = activity_durations[activities[a]]
    max_grps = activity_group_limits[activities[a]]

    if dur > 1:
        for d in days:
            num_slots = len(day_blocks[d])
            for t in range(num_slots):
                for k in range(1, dur):
                    if t + k < num_slots:
                        for g in range(num_groups):
                            row_dict = {get_var_idx(g, a, d, t): max_grps}
                            for g_prime in range(num_groups):
                                idx = get_var_idx(g_prime, a, d, t + k)
                                row_dict[idx] = row_dict.get(idx, 0) + 1
                            add_constraint(row_dict, 0, max_grps)

# G. Activity-Specific Cooldown / Gap Times
gap_rules = {"Tea Party": 4}

for a in range(num_activities):
    act_name = activities[a]
    if act_name in gap_rules:
        gap = gap_rules[act_name]
        dur = activity_durations[act_name]
        max_grps = activity_group_limits[act_name]

        for d in days:
            num_slots = len(day_blocks[d])
            for t in range(num_slots):
                for k in range(1, dur + gap):
                    if t + k < num_slots:
                        for g in range(num_groups):
                            row_dict = {get_var_idx(g, a, d, t): max_grps}
                            for g_prime in range(num_groups):
                                idx = get_var_idx(g_prime, a, d, t + k)
                                row_dict[idx] = row_dict.get(idx, 0) + 1
                            add_constraint(row_dict, 0, max_grps)

# Combine sparse rows into a single Compressed Sparse Row matrix
A_sparse = csr_matrix((A_vals, (A_rows, A_cols)), shape=(current_row, num_vars))
unified_constraints = LinearConstraint(A_sparse, lb_list, ub_list)

# ==========================================
# 4. SOLVER EXECUTION
# ==========================================
# Pass the single unified block constraint instead of a massive list
res = milp(c=c, constraints=unified_constraints, integrality=integrality, bounds=bounds)

# ==========================================
# 5. USER-FRIENDLY STRING FORMATTED OUTPUT
# ==========================================


if res.success:
    print("Camp Schedule Found. Generating files...\n")
    sol = res.x

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
