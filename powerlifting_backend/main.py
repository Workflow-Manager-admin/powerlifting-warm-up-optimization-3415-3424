from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, conint, confloat, validator
from typing import List, Any, Dict
from powerlifting_backend.utils import (
    calculate_warmup_sets,
    predict_max_reps
)
import os

app = FastAPI(
    title="Powerlifting Warm-Up and Max Rep Calculator",
    description="REST API for powerlifting warm-up recommendations and max rep prediction based on RPE and established formulas.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Calculation", "description": "Endpoints for warm-up and max rep calculation"}
    ]
)

# === Input/Output Models ===

class WarmupRequest(BaseModel):
    rpe: confloat(ge=5.0, le=10.0) = Field(..., description="Rating of Perceived Exertion (5.0 to 10.0)")
    weight: confloat(gt=0) = Field(..., description="Top set weight in kilograms (must be positive)")
    reps: conint(gt=0, le=20) = Field(..., description="Number of reps in top set (1–20)")
    # PUBLIC_INTERFACE
    @validator("rpe")
    def round_rpe(cls, v):
        # Only common RPE values usually allowed in 0.5 increments
        rounded = round(v * 2) / 2
        if rounded < 5 or rounded > 10:
            raise ValueError("RPE must be between 5.0 and 10.0 (in 0.5 increments)")
        return rounded

class WarmupSet(BaseModel):
    set_number: int
    weight: float
    reps: int
    description: str

class WarmupResponse(BaseModel):
    warmup_sets: List[WarmupSet]

class MaxRepsRequest(BaseModel):
    weight: confloat(gt=0) = Field(..., description="Weight in kilograms (must be positive)")
    rpe: confloat(ge=5.0, le=10.0) = Field(..., description="RPE between 5.0 and 10.0")
    # PUBLIC_INTERFACE
    @validator("rpe")
    def round_rpe(cls, v):
        rounded = round(v * 2) / 2
        if rounded < 5 or rounded > 10:
            raise ValueError("RPE must be between 5.0 and 10.0 (in 0.5 increments)")
        return rounded

class MaxRepsResponse(BaseModel):
    predicted_max_reps: int

# === Endpoints ===

# PUBLIC_INTERFACE
@app.post(
    "/api/calculate-warmup",
    response_model=WarmupResponse,
    tags=["Calculation"],
    summary="Calculate recommended warm-up sets",
    description="""
Calculate powerlifting warm-up sets based on RPE, weight, and reps.

**Example payload:**
```
{
    "rpe": 8,
    "weight": 140,
    "reps": 5
}
```

**Expected response:**
```
{
  "warmup_sets": [
    {"set_number": 1, "weight": 70.0, "reps": 5, "description": "50% of top set"},
    {"set_number": 2, "weight": 98.0, "reps": 3, "description": "70% of top set"},
    {"set_number": 3, "weight": 112.0, "reps": 2, "description": "80% of top set"},
    {"set_number": 4, "weight": 126.0, "reps": 1, "description": "90% of top set"}
  ]
}
```
""",
    responses={
        422: {"description": "Validation error"},
        400: {"description": "Calculation error"},
    }
)
async def calculate_warmup(req: WarmupRequest):
    """
    Receives rpe, top set weight (kg), and reps, and returns a list of recommended warm-up sets
    """
    try:
        warmup_sets = calculate_warmup_sets(req.rpe, req.weight, req.reps)
        return {"warmup_sets": warmup_sets}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# PUBLIC_INTERFACE
@app.post(
    "/api/max-reps",
    response_model=MaxRepsResponse,
    tags=["Calculation"],
    summary="Predict maximum reps for a given weight and RPE",
    description="""
Estimate max repetitions possible at a given weight and RPE.

**Example payload:**
```
{
    "weight": 100,
    "rpe": 9
}
```

**Expected response:**
```
{
  "predicted_max_reps": 5
}
```
""",
    responses={
        422: {"description": "Validation error"},
        400: {"description": "Calculation error"},
    }
)
async def max_reps(req: MaxRepsRequest):
    """
    Receives weight (kg) and RPE, returns max predicted reps as integer.
    """
    try:
        reps = predict_max_reps(req.weight, req.rpe)
        return {"predicted_max_reps": reps}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)}


# --- Entrypoint for uvicorn ---
# Allow running with: python -m powerlifting_backend.main or `uvicorn powerlifting_backend.main:app`
if __name__ == "__main__":
    import uvicorn
    # Use port 8000 by default or read PORT env
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("powerlifting_backend.main:app", host="0.0.0.0", port=port, reload=True)
