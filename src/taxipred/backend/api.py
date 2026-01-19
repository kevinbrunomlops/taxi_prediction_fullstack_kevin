import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Literal

from taxipred.backend.data_processing import TaxiData
from taxipred.utils.constants import MODEL_PATH


TimeOfDay = Literal["Morning", "Afternoon", "Evening", "Night"]

app = FastAPI(title="Taxi Prediction API")

data = TaxiData()
model = joblib.load(MODEL_PATH)


class PredictIn(BaseModel):
    Trip_Distance_km: float = Field(..., ge=0)
    Trip_Duration_Minutes: float = Field(..., ge=0)
    Time_of_Day: TimeOfDay
    Passenger_Count: float = Field(..., ge=0)

@app.get("/health")
def health():
    return{
        "status" : "ok",
        "rows": len(data.df),
        "model_path": str(MODEL_PATH),
    }

@app.get("/data/sample")
def sample(n: int = Query(10, ge=1, le=200)):
    return data.sample(n)

@app.get("/data/rows")
def rows(
    offset: int = 0,
    limit: int = 50,
    columns: str | None = None,
    time_of_day: TimeOfDay | None = None,
):
    cols = columns.split(",") if columns else None
    return data.rows(offset, limit, cols, time_of_day)

@app.get("/data/stats")
def stats():
    return data.stats()


@app.post("/predict")
def predict(x:PredictIn):
    try:
        X = data.make_X(
            x.Trip_Distance_km,
            x.Trip_Duration_Minutes,
            x.Time_of_Day,
            x.Passenger_Count,
        )
        return {"prediction": float(model.predict(X)[0])}
    except Exception as e: 
        raise HTTPException(500, str(e))
    
@app.post("/predict/batch")
def predicts_batch(items: list[PredictIn]):
    X = pd.DataFrame([i.model_dump() for i in items])
    return {"precitions": [float(v) for v in model.predict(X)]}