import numpy as np
import os
import schedule_utils
from datetime import datetime, timedelta
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import csr_matrix

def solver(day_blocks, boys_group_ages, girls_group_ages, activities_list, travel_matrix):
    days = list(day_blocks.keys())
    groups = list(boys_group_ages.keys()) + list(girls_group_ages.keys())
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
        nonlocal current_row
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
    return milp(c=c, constraints=unified_constraints, integrality=integrality, bounds=bounds), {
        "num_groups": num_groups,
        "num_activities": num_activities,
        "activity_durations": activity_durations,
        "activities": activities,
        "days": days,
        "get_var_idx": get_var_idx,
        "groups": groups,
    }
