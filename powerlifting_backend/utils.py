from typing import List, Dict
import math

# RPE Table based on Mike Tuchscherer's chart, as percentage of 1RM at each rep/RPE
RPE_PERCENT_TABLE = {
    # e.g. 5 reps at RPE 10 = about 86%
    10:  {1: 100, 2: 95, 3: 92, 4: 89, 5: 86, 6: 84, 7: 81, 8: 79, 9: 76, 10: 74},
    9.5: {1: 98, 2: 94, 3: 91, 4: 88, 5: 85, 6: 82, 7: 80, 8: 77, 9: 75, 10: 72},
    9:   {1: 96, 2: 92, 3: 89, 4: 86, 5: 84, 6: 81, 7: 79, 8: 76, 9: 74, 10: 71},
    8.5: {1: 94, 2: 89, 3: 87, 4: 84, 5: 81, 6: 79, 7: 76, 8: 74, 9: 71, 10: 69},
    8:   {1: 92, 2: 87, 3: 84, 4: 81, 5: 79, 6: 76, 7: 74, 8: 71, 9: 69, 10: 66},
    7.5: {1: 89, 2: 84, 3: 81, 4: 79, 5: 76, 6: 74, 7: 71, 8: 69, 9: 66, 10: 64}
}

def _lookup_percent(rpe: float, reps: int) -> float:
    """Return %1RM for given RPE and reps; fallback to Epley formula if outside chart."""
    rpe = round(rpe * 2) / 2
    reps = int(reps)
    pct = None
    if rpe in RPE_PERCENT_TABLE and reps in RPE_PERCENT_TABLE[rpe]:
        pct = RPE_PERCENT_TABLE[rpe][reps] / 100.0
    if pct is None:
        # Fallback: estimate %1RM using Epley formula 1RM and back-calculate percent
        pct = 1 / (1 + 0.0333 * (reps - 1))
    return pct

# PUBLIC_INTERFACE
def calculate_warmup_sets(rpe: float, weight: float, reps: int) -> List[Dict]:
    """
    Calculate warmup sets based on top set data (weight, RPE, reps).
    Returns a list of warmup sets, each with set_number, weight, reps, and description.
    Uses established protocols: e.g., 50%, 70%, 80%, 90% of top set.
    """

    if not (5.0 <= rpe <= 10.0):
        raise ValueError("RPE must be 5.0–10.0")
    if weight <= 0:
        raise ValueError("Weight must be positive")
    if not (1 <= reps <= 20):
        raise ValueError("Reps must be 1–20")

    warmup_percentages = [(0.5, 5, "50% of top set"),
                          (0.7, 3, "70% of top set"),
                          (0.8, 2, "80% of top set"),
                          (0.9, 1, "90% of top set")]
    warmup_sets = []
    for idx, (pct, warm_reps, descr) in enumerate(warmup_percentages, start=1):
        set_weight = round(weight * pct / 2.5) * 2.5  # round to nearest 2.5kg
        warmup_sets.append({
            "set_number": idx,
            "weight": set_weight,
            "reps": warm_reps,
            "description": descr,
        })
    return warmup_sets

# PUBLIC_INTERFACE
def predict_max_reps(weight: float, rpe: float) -> int:
    """
    Predict max number of reps the lifter can do at given weight and RPE using %1RM tables.
    Returns an integer number of reps (best guess).
    """
    if weight <= 0:
        raise ValueError("Weight must be positive")
    if not (5.0 <= rpe <= 10.0):
        raise ValueError("RPE must be 5.0–10.0")
    # Assume 1RM can be estimated by the Epley formula using a RPE 10 single
    # Reverse-calculate expected %1RM for the given RPE at different reps,
    # until the calculated %1RM x 1RM matches the input weight
    # We'll try reps 1–15 and pick the closest
    min_diff = float('inf')
    best_reps = 1
    for test_reps in range(1, 16):
        pct = _lookup_percent(rpe, test_reps)
        est_1rm = weight / pct if pct > 0 else 0
        # Check what weight this would produce for those reps at this RPE
        calc_weight = est_1rm * pct
        diff = abs(calc_weight - weight)
        if diff < min_diff:
            min_diff = diff
            best_reps = test_reps
    return best_reps
