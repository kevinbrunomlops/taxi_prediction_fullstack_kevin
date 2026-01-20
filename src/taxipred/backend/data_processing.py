from taxipred.utils.constants import TAXI_CLEANED_CSV
import pandas as pd
import json


FEATURES = [
    "Trip_Distance_km",
    "Trip_Duration_Minutes",
    "Time_of_Day",
    "Passenger_Count",
]
TARGET = "Trip_Price"


class TaxiData:
    def __init__(self, path: str = TAXI_CLEANED_CSV):
        if not path.exists():
            raise FileNotFoundError(f"Missing data file: {path}")
        self.df = pd.read_csv(path)

        for c in [*FEATURES, TARGET]:
            if c in self.df.columns and c != "Time_of_Day":
                self.df[c] = pd.to_numeric(self.df[c], errors="coerce")
            if "Time_of_Day" in self.df.columns:
                self.df["Time_of_Day"] = self.df["Time_of_Day"].astype(str).str.strip()

            keep = [c for c in FEATURES if c in self.df.columns]
            if keep:
                self.df = self.df.dropna(subset=keep).reset_index(drop=True)

    def rows(self, offset=0, limit=50, columns=None, time_of_day=None):
        df = self.df
        if time_of_day:
            if "Time_of_Day" not in df.columns:
                raise ValueError("No Time_of_Day column in dataset.")
            df = df[df["Time_of_Day"] == time_of_day]

        total = len(df)
        offset, limit = max(0, int(offset)), max(1, min(int(limit), 500))
        df = df.iloc[offset : offset + limit]

        if columns:
            cols = [c for c in columns if c in df.columns]
            if not cols:
                raise ValueError("Requested columns not found.")
            df = df[cols]

        return {
            "offset": offset,
            "limit": limit,
            "total": total,
            "returned": len(df),
            "rows": df.to_dict("records"),
        }

    def sample(self, n=10):
        n = max(1, min(int(n), len(self.df)))
        return self.df.head(n).to_dict("records")

    def stats(self):
        out = {"n_rows": int(len(self.df)), "n_cols": int(self.df.shape[1])}
        num = [c for c in self.df.columns if pd.api.types.is_numeric_dtype(self.df[c])]
        if num:
            out["numeric_describe"] = self.df[num].describe().to_dict()
        if "Time_of_Day" in self.df.columns:
            out["time_of_day_counts"] = self.df["Time_of_Day"].value_counts().to_dict()
            out["time_of_day_values"] = sorted(
                self.df["Time_of_Day"].dropna().unique().tolist()
            )
        return out

    def make_X(
        self, Trip_Distance_km, Trip_Duration_Minutes, Time_of_Day, Passenger_Count
    ):
        return pd.DataFrame(
            [
                {
                    "Trip_Distance_km": float(Trip_Distance_km),
                    "Trip_Duration_Minutes": float(Trip_Duration_Minutes),
                    "Passenger_Count": float(Passenger_Count),
                    "Time_of_Day": str(Time_of_Day).strip(),
                }
            ]
        )

    def to_json(self):
        return json.loads(self.df.to_json(orient="records"))
