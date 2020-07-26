'''
Create regression model for year_sprout / prediction based on
X: genus, bole_radius
y: year_sprout
'''
'''
Make model for age prediction
X: genus, bole radius
y: age (year_sprout)
'''
import json
import pickle
from statistics import median, mean
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler
from sklearn.ensemble import GradientBoostingRegressor


MODEL_DATA_DIR = "../../data/predictions_models"
MODEL = None
LABEL_ENCODER = None
SCALER = None


def _load_train_data() -> List[Dict[str, Any]]:
    with open("../../data/predictions_data/genus_bole_radius_year_planted.json") as f:
        train_data_raw = json.load(f)

    train_data_list = []
    for genus, genus_vals in train_data_raw.items():
        for bole_radius, year_planted_vals in genus_vals.items():
            if len(year_planted_vals.keys()) < 5:
                continue

            collected_years = []
            tmp_data_list = []
            for year_planted, num in year_planted_vals.items():
                # tmp. 
                if int(year_planted) < 1800:
                    continue
                if int(year_planted) > 2020:
                    continue
                if int(bole_radius) > 150:
                    continue
                
                for i in range(num):
                    tmp_data_list.append({
                        "genus": genus,
                        "bole_radius": int(bole_radius),
                        "year_sprout": int(year_planted) - 10
                    })
                    collected_years.append(int(year_planted) - 10)
            
            median_year_sprout = int(median(collected_years))
            del_index = []
            for i, tmp in enumerate(tmp_data_list):
                if tmp["year_sprout"] < (median_year_sprout - 10) or tmp["year_sprout"] > (median_year_sprout + 10):
                    del_index.append(i)
            
            for i in range(len(del_index)-1, -1, -1):
                idx = del_index[i]
                del tmp_data_list[idx]
            
            if len(tmp_data_list) > 0:
                train_data_list += tmp_data_list
    
    return train_data_list


def train_model() -> None:
    df = pd.DataFrame(_load_train_data())
    
    label_encoder = LabelEncoder()
    scaler = MinMaxScaler()  #StandardScaler()
    
    model = GradientBoostingRegressor(learning_rate=0.01, max_depth=6, min_samples_split=5, n_estimators=500)  

    df["encoded_genus"] = label_encoder.fit_transform(df["genus"].astype(str))
    df["bole_radius_scaled"] = scaler.fit_transform(df[["bole_radius"]])
    
    X_train = df[["bole_radius_scaled", "encoded_genus"]].to_numpy()
    y_train = df[["year_sprout"]].to_numpy().ravel()

    model.fit(X_train, y_train)

    pickle.dump(label_encoder, open(f"{MODEL_DATA_DIR}/age_regression_label_encoder.pkl", 'wb'))
    pickle.dump(scaler, open(f"{MODEL_DATA_DIR}/age_regression_scaler.pkl", 'wb'))
    pickle.dump(model, open(f"{MODEL_DATA_DIR}/age_regression_model.pkl", 'wb'))


def predict_year_sprout(genus: str, bole_radius: int) -> int:
    global MODEL
    global LABEL_ENCODER
    global SCALER

    if MODEL is None:
        MODEL = pickle.load(open(f"{MODEL_DATA_DIR}/age_regression_model.pkl", "rb"))
    if LABEL_ENCODER is None:
        LABEL_ENCODER = pickle.load(open(f"{MODEL_DATA_DIR}/age_regression_label_encoder.pkl", "rb"))
    if SCALER is None:
        SCALER = pickle.load(open(f"{MODEL_DATA_DIR}/age_regression_scaler.pkl", "rb"))

    
    df = pd.DataFrame(data={"genus": [genus], "bole_radius": [bole_radius]})
    df["encoded_genus"] = LABEL_ENCODER.transform(df["genus"].astype(str))
    df["bole_radius_scaled"] = SCALER.transform(df[["bole_radius"]])

    X_pred = df[["bole_radius_scaled", "encoded_genus"]].to_numpy()
    predictions = MODEL.predict(X_pred)

    for i, p in enumerate(predictions):
        return round(p)

    

if __name__ == "__main__":
    train_model()

    # tests
    genus = "Taxus"  # "Robinia" # "Platanus"
    for bole_radius in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 100, 150]:
        print(bole_radius, predict_year_sprout(genus, bole_radius))
    
