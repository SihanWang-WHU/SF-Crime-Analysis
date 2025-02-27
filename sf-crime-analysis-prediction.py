#!/usr/bin/env python
# coding: utf-8

"""
sf_crime_analysis.py

This script performs San Francisco crime data analysis and prediction. It includes:
1. Data loading and basic cleaning
2. Feature engineering
3. Training a LightGBM multi-class model
4. Generating submission results

At the end of execution, it reports the runtime for each major step.
Use requirements.txt for dependencies.
"""

import warnings
warnings.filterwarnings("ignore")

import time
import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder
from lightgbm import LGBMClassifier

def load_kaggle_data(train_path, test_path):
    print("[INFO] Loading train and test data...")
    train = pd.read_csv(train_path, parse_dates=['Dates'])
    test = pd.read_csv(test_path, parse_dates=['Dates'], index_col='Id')
    print(f"[INFO] Train shape: {train.shape}, Test shape: {test.shape}")

    before_dedup = len(train)
    train.drop_duplicates(inplace=True)
    after_dedup = len(train)
    if (before_dedup - after_dedup) > 0:
        print(f"[INFO] Removed {before_dedup - after_dedup} duplicate rows from train")

    # Replace invalid coordinates with NaN
    train.replace({'X': -120.5, 'Y': 90.0}, np.nan, inplace=True)
    test.replace({'X': -120.5, 'Y': 90.0}, np.nan, inplace=True)

    # Impute missing coords by PdDistrict
    imp = SimpleImputer(strategy='mean')
    for district in train['PdDistrict'].unique():
        cond_train = (train['PdDistrict'] == district)
        cond_test = (test['PdDistrict'] == district)
        train.loc[cond_train, ['X', 'Y']] = imp.fit_transform(train.loc[cond_train, ['X', 'Y']])
        test.loc[cond_test, ['X', 'Y']] = imp.transform(test.loc[cond_test, ['X', 'Y']])

    return train, test

def feature_engineering(data):
    print("[INFO] Feature engineering...")
    data['Date'] = pd.to_datetime(data['Dates'].dt.date)
    data['n_days'] = (data['Date'] - data['Date'].min()).dt.days
    data['Day'] = data['Dates'].dt.day
    data['DayOfWeek'] = data['Dates'].dt.weekday
    data['Month'] = data['Dates'].dt.month
    data['Year'] = data['Dates'].dt.year
    data['Hour'] = data['Dates'].dt.hour
    data['Minute'] = data['Dates'].dt.minute

    data['Block'] = data['Address'].str.contains('block', case=False).astype(int)

    for col in ['Dates', 'Date', 'Address']:
        if col in data.columns:
            data.drop(columns=col, inplace=True)

    return data

def train_model(train_df, test_df, submission_csv='LGBM_final.csv'):
    print("[INFO] Preparing data for training...")
    for col in ['Descript', 'Resolution']:
        if col in train_df.columns:
            train_df.drop(columns=col, inplace=True)

    train_df = feature_engineering(train_df)
    test_df = feature_engineering(test_df)

    # Encode categorical features
    le_district = LabelEncoder()
    train_df['PdDistrict'] = le_district.fit_transform(train_df['PdDistrict'])
    test_df['PdDistrict'] = le_district.transform(test_df['PdDistrict'])

    le_category = LabelEncoder()
    y = le_category.fit_transform(train_df.pop('Category'))
    X = train_df

    print(f"[INFO] Training shape: {X.shape}, classes: {len(np.unique(y))}")

    # Adjusted LightGBM parameters
    model = LGBMClassifier(
        objective='multiclass',
        num_class=len(np.unique(y)),
        boosting_type='gbdt',
        learning_rate=0.1,
        num_leaves=31,
        min_data_in_leaf=20,
        max_bin=255,
        max_delta_step=0.9,
        n_estimators=300
    )

    print("[INFO] Fitting LightGBM model...")
    model.fit(X, y, categorical_feature=['PdDistrict'])

    print("[INFO] Predicting on test set...")
    test_pred = model.predict_proba(test_df)

    categories = le_category.inverse_transform(range(len(le_category.classes_)))
    submission = pd.DataFrame(test_pred, columns=categories, index=test_df.index)
    submission.to_csv(submission_csv, index_label='Id')
    print(f"[INFO] Submission saved to '{submission_csv}'")

def main():
    overall_start = time.time()

    train_path = './Data/train_kaggle_sample.csv'
    test_path = './Data/test_kaggle_sample.csv'
    output_csv = 'LGBM_final.csv'

    print("[INFO] Starting SF Crime Analysis...")

    # Step 1: Load data
    step1_start = time.time()
    train_df, test_df = load_kaggle_data(train_path, test_path)
    step1_time = time.time() - step1_start

    # Step 2: Train model
    step2_start = time.time()
    train_model(train_df, test_df, submission_csv=output_csv)
    step2_time = time.time() - step2_start

    total_time = time.time() - overall_start

    # Final time report
    print("[INFO] ----- RUNTIME REPORT -----")
    print(f"[INFO] Step 1 (Loading data): {step1_time:.2f} seconds")
    print(f"[INFO] Step 2 (Training model): {step2_time:.2f} seconds")
    print(f"[INFO] Total runtime: {total_time:.2f} seconds")

if __name__ == "__main__":
    main()
