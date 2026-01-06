"""
Aadhaar Real Data Processing & Analysis
=======================================
Reads split CSVs from api_data_* folders, aggregates them, 
and generates real insights for the dashboard.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import json
import os
import glob

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = '/home/harsh/Downloads/Hackathon'
OUTPUT_DIR = os.path.join(BASE_DIR, 'dashboard/data')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Data Folders
BIO_DIR = os.path.join(BASE_DIR, 'api_data_aadhar_biometric')
DEMO_DIR = os.path.join(BASE_DIR, 'api_data_aadhar_demographic')
ENROL_DIR = os.path.join(BASE_DIR, 'api_data_aadhar_enrolment')

# ============================================================================
# DATA LOADING & AGGREGATION
# ============================================================================

def load_and_aggregate_folder(folder_path, value_cols):
    """
    Reads all CSVs in a folder, aggregates by state, district, pincode.
    Returns a grouped DataFrame.
    """
    print(f"📂 Scanning {folder_path}...")
    all_files = glob.glob(os.path.join(folder_path, "*.csv"))
    
    if not all_files:
        print(f"   ⚠️ No CSV files found in {folder_path}")
        return pd.DataFrame(columns=['state', 'district', 'pincode'] + value_cols)

    df_list = []
    for filename in all_files:
        try:
            # Read only necessary columns to save memory
            cols = ['state', 'district', 'pincode'] + value_cols
            curr_df = pd.read_csv(filename, usecols=lambda c: c in cols)
            
            # Clean column names (strip whitespace)
            curr_df.columns = [c.strip() for c in curr_df.columns]
            
            # Ensure value columns are numeric
            for col in value_cols:
                if col in curr_df.columns:
                    curr_df[col] = pd.to_numeric(curr_df[col], errors='coerce').fillna(0)
            
            df_list.append(curr_df)
        except Exception as e:
            print(f"   ❗ Error reading {filename}: {e}")

    if not df_list:
        return pd.DataFrame()

    print(f"   combining {len(df_list)} files...")
    full_df = pd.concat(df_list, ignore_index=True)
    
    # Clean string columns
    for col in ['state', 'district']:
        full_df[col] = full_df[col].astype(str).str.strip().str.title()
    
    # Aggregate
    print(f"   aggregating by geo-location...")
    agg_df = full_df.groupby(['state', 'district', 'pincode'])[value_cols].sum().reset_index()
    
    print(f"   ✅ Loaded and aggregated: {len(agg_df):,} records")
    return agg_df

def build_master_dataset():
    """
    Loads data from all three sources and merges them into a master DataFrame.
    """
    print("\n🏗️ Building Master Dataset from Real Data...")
    
    # 1. Load Biometric Data
    # Expected cols: bio_age_5_17, bio_age_17_
    bio_cols = ['bio_age_5_17', 'bio_age_17_']
    df_bio = load_and_aggregate_folder(BIO_DIR, bio_cols)
    
    # 2. Load Demographic Data
    # Expected cols: demo_age_5_17, demo_age_17_
    demo_cols = ['demo_age_5_17', 'demo_age_17_']
    df_demo = load_and_aggregate_folder(DEMO_DIR, demo_cols)
    
    # 3. Load Enrolment Data
    # Expected cols: age_0_5, age_5_17, age_18_greater
    enrol_cols = ['age_0_5', 'age_5_17', 'age_18_greater']
    df_enrol = load_and_aggregate_folder(ENROL_DIR, enrol_cols)
    
    # 4. Merge DataFrames
    # Outer join to ensure we capture all locations
    print("\n🔗 Merging datasets...")
    
    if df_bio.empty and df_demo.empty and df_enrol.empty:
        print("❌ No data loaded from any source!")
        return pd.DataFrame()

    # Start with enrollment or whichever is largest, but outer join is safest
    # Using pandas merge with outer join on keys
    merge_keys = ['state', 'district', 'pincode']
    
    # Merge Bio + Demo
    master_df = pd.merge(df_bio, df_demo, on=merge_keys, how='outer')
    
    # Merge result + Enrolment
    master_df = pd.merge(master_df, df_enrol, on=merge_keys, how='outer')
    
    # Fill NaN with 0 for all metric columns
    numeric_cols = bio_cols + demo_cols + enrol_cols
    master_df[numeric_cols] = master_df[numeric_cols].fillna(0)
    
    print(f"   ✅ Master Dataset ready: {len(master_df):,} rows")
    return master_df

# ============================================================================
# ANALYSIS LOGIC (Reused/Adapted)
# ============================================================================

def identify_maintenance_deserts(df, threshold=0.2):
    print("\n📊 Identifying Maintenance Deserts...")
    district_summary = df.groupby('district')[['age_5_17', 'bio_age_5_17']].sum().reset_index()
    
    district_summary['update_ratio'] = district_summary.apply(
        lambda row: row['bio_age_5_17'] / row['age_5_17'] if row['age_5_17'] > 0 else 0,
        axis=1
    )
    
    deserts = district_summary[district_summary['update_ratio'] < threshold].copy()
    deserts['risk_score'] = 1 - deserts['update_ratio']
    deserts = deserts.sort_values('risk_score', ascending=False)
    
    print(f"   ✅ Found {len(deserts)} Maintenance Deserts")
    return deserts

def identify_migration_hotspots(df, min_ratio=10):
    print("\n📊 Identifying Migration Hotspots...")
    summary = df.groupby(['state', 'district'])[['demo_age_17_', 'age_18_greater']].sum().reset_index()
    
    summary['migration_ratio'] = summary.apply(
        lambda row: min(row['demo_age_17_'] / row['age_18_greater'], 1000000) 
                    if row['age_18_greater'] > 0 else 0,
        axis=1
    )
    
    hotspots = summary[summary['migration_ratio'] > min_ratio].copy()
    hotspots = hotspots.sort_values('migration_ratio', ascending=False)
    
    print(f"   ✅ Found {len(hotspots)} Migration Hotspots")
    return hotspots

def predict_update_surge(df):
    print("\n📊 Predicting Mandatory Update Surge...")
    surge = df.groupby('state')['age_0_5'].sum().reset_index()
    surge.columns = ['state', 'projected_surge']
    surge = surge.sort_values('projected_surge', ascending=False)
    print(f"   ✅ Total projected surge: {surge['projected_surge'].sum():,.0f}")
    return surge

def calculate_priority_scores(df):
    print("\n📊 Calculating Priority Scores (DRAM)...")
    
    pincode_data = df.groupby(['pincode', 'state', 'district']).agg({
        'age_5_17': 'sum', 'bio_age_5_17': 'sum',
        'demo_age_17_': 'sum', 'age_18_greater': 'sum',
        'age_0_5': 'sum'
    }).reset_index()
    
    # Maintenance Risk
    pincode_data['maintenance_risk'] = pincode_data.apply(
        lambda row: 1 - (row['bio_age_5_17'] / row['age_5_17']) if row['age_5_17'] > 0 else 1, axis=1
    )
    
    # Migration Impact
    pincode_data['migration_impact'] = pincode_data.apply(
        lambda row: row['demo_age_17_'] / row['age_18_greater'] if row['age_18_greater'] > 0 else 0, axis=1
    )
    # Clip migration impact
    max_mig = pincode_data['migration_impact'].replace([np.inf], np.nan).max()
    if pd.isna(max_mig): max_mig = 1
    pincode_data['migration_impact'] = pincode_data['migration_impact'].clip(upper=max_mig * 2)
    
    # Normalize
    scaler = MinMaxScaler()
    cols = ['maintenance_risk', 'migration_impact', 'age_0_5']
    # Check if empty
    if not pincode_data.empty:
        pincode_data[['norm_maint', 'norm_mig', 'norm_surge']] = scaler.fit_transform(pincode_data[cols])
        
        pincode_data['priority_score'] = (
            pincode_data['norm_maint'] + pincode_data['norm_mig'] + pincode_data['norm_surge']
        ) / 3
    else:
        pincode_data['priority_score'] = 0

    print(f"   ✅ Calculated scores for {len(pincode_data):,} pincodes")
    return pincode_data

def calculate_welfare_risk(df):
    print("\n📊 Calculating Welfare Risk Scores...")
    df_copy = df.copy()
    df_copy['risk_score'] = df_copy['age_5_17'] - df_copy['bio_age_5_17']
    # If negative (more updates than enrolment? possible if data mismatch, set to 0)
    df_copy['risk_score'] = df_copy['risk_score'].clip(lower=0)
    
    welfare_risk = df_copy.groupby('district')['risk_score'].sum().reset_index()
    welfare_risk.columns = ['district', 'welfare_risk_score']
    welfare_risk = welfare_risk.sort_values('welfare_risk_score', ascending=False)
    return welfare_risk

def calculate_fiscal_risk(welfare_risk, df_dist_state, per_child_cost=2500):
    print("\n📊 Calculating Fiscal Risk...")
    fiscal_data = welfare_risk.merge(df_dist_state, on='district', how='left')
    fiscal_data['fiscal_risk'] = fiscal_data['welfare_risk_score'] * per_child_cost
    
    state_fiscal = fiscal_data.groupby('state')['fiscal_risk'].sum().reset_index()
    state_fiscal.columns = ['state', 'total_fiscal_risk']
    state_fiscal = state_fiscal.sort_values('total_fiscal_risk', ascending=False)
    return state_fiscal

def generate_recommendations(priority_pincodes, df, top_n=50):
    print("\n📊 Generating Recommendations...")
    if priority_pincodes.empty:
        return pd.DataFrame()

    # Calculate Total Activity for each pincode
    # (activity = total updates + enrolments)
    pincode_activity = df.groupby('pincode').agg({
        'demo_age_5_17': 'sum', 'demo_age_17_': 'sum',
        'bio_age_5_17': 'sum', 'bio_age_17_': 'sum',
        'age_0_5': 'sum', 'age_5_17': 'sum', 'age_18_greater': 'sum'
    }).reset_index() # Simplified activity metric
    
    pincode_activity['total_activity'] = (
        pincode_activity['bio_age_5_17'] + 
        pincode_activity['bio_age_17_'] + 
        pincode_activity['age_0_5'] + 
        pincode_activity['age_18_greater']
    )

    top_list = priority_pincodes.sort_values('priority_score', ascending=False).head(top_n)
    top_list = top_list.merge(pincode_activity[['pincode', 'total_activity']], on='pincode', how='left')
    
    p75 = pincode_activity['total_activity'].quantile(0.75) if not pincode_activity.empty else 100
    p25 = pincode_activity['total_activity'].quantile(0.25) if not pincode_activity.empty else 10
    
    def recommend(row):
        act = row['total_activity']
        if pd.isna(act) or act < p25: return 'Mobile Outreach Van'
        if act > p75: return 'Aadhaar Seva Kendra (ASK)'
        return 'Hybrid Approach'
        
    top_list['recommendation'] = top_list.apply(recommend, axis=1)
    return top_list

# ============================================================================
# MAIN
# ============================================================================

def main():
    df = build_master_dataset()
    
    if df.empty:
        print("❌ Aborting analysis due to no data.")
        return

    # Run Analysis
    maint_deserts = identify_maintenance_deserts(df)
    mig_hotspots = identify_migration_hotspots(df)
    surge_data = predict_update_surge(df)
    
    # Priority Scores (Pincode level)
    priority_df = calculate_priority_scores(df) # Contains state, district, pincode
    
    welfare_df = calculate_welfare_risk(df)
    
    # District-State mapping for fiscal risk
    dist_state_map = df[['district', 'state']].drop_duplicates()
    fiscal_df = calculate_fiscal_risk(welfare_df, dist_state_map)
    
    recs_df = generate_recommendations(priority_df, df)
    
    # State Priority (for Heatmap)
    # Check if 'priority_score' exists and we have state info
    if 'priority_score' in priority_df.columns and 'state' in priority_df.columns:
        state_priority = priority_df.groupby('state')['priority_score'].mean().reset_index()
        state_priority = state_priority.sort_values('priority_score', ascending=False)
    else:
        state_priority = pd.DataFrame()

    # Prepare JSON Output
    output_data = {
        'summary': {
            'total_records': int(len(df)),
            'total_pincodes': int(df['pincode'].nunique()),
            'total_districts': int(df['district'].nunique()),
            'total_states': int(df['state'].nunique()),
            'maintenance_deserts_count': int(len(maint_deserts)),
            'migration_hotspots_count': int(len(mig_hotspots)),
            'total_projected_surge': int(surge_data['projected_surge'].sum()) if not surge_data.empty else 0,
            'total_fiscal_risk': float(fiscal_df['total_fiscal_risk'].sum()) if not fiscal_df.empty else 0.0
        },
        'maintenance_deserts': maint_deserts.head(50).to_dict(orient='records'),
        'migration_hotspots': mig_hotspots.head(50).to_dict(orient='records'),
        'update_surge': surge_data.head(50).to_dict(orient='records'),
        'top_priority_pincodes': priority_df.sort_values('priority_score', ascending=False)
                                            .head(50)[['pincode', 'state', 'district', 'priority_score', 'maintenance_risk', 'migration_impact', 'age_0_5']]
                                            .to_dict(orient='records'),
        'state_priority': state_priority.to_dict(orient='records'),
        'state_fiscal_risk': fiscal_df.to_dict(orient='records'),
        'welfare_risk_districts': welfare_df.head(50).to_dict(orient='records'),
        'recommendations': recs_df.to_dict(orient='records'),
        'action_plan': [
            {
                'title': 'DBT Shield Mobile Camps',
                'description': 'Deploy mobile biometric camps in Maintenance Deserts.',
                'target': 'High-risk pincodes with low activity',
                'priority': 'Critical'
            },
            {
                'title': 'Migrant Connect Centers',
                'description': 'Establish multi-lingual facilitation centers in Migration Hotspots.',
                'target': 'Districts with high demographic updates',
                'priority': 'High'
            },
            {
                'title': 'Future Ready School Program',
                'description': 'School-based biometric drives for children aging into mandatory updates.',
                'target': 'States with high projected surge',
                'priority': 'Medium'
            },
            {
                'title': 'Performance-Based Allocation',
                'description': 'Dynamic resource allocation based on real-time priority scores.',
                'target': 'All districts',
                'priority': 'Ongoing'
            }
        ],
        'full_state_stats': [] # Placeholder for map data if needed detailed, 
                               # but 'state_priority' and 'update_surge' are mostly enough.
                               # Lets add a consolidated state object for the map.
    }
    
    # Create consolidated state stats for map
    # We want: State Name -> { priority_score, surge, enrollment, updates, etc }
    state_stats = {}
    
    # 1. Base State List
    all_states = df['state'].unique()
    
    # Helper to get value from df
    def get_val(src_df, state_key, col):
        row = src_df[src_df['state'] == state_key]
        if not row.empty:
            return row.iloc[0][col]
        return 0

    for state in all_states:
        s_prio = get_val(state_priority, state, 'priority_score')
        s_surge = get_val(surge_data, state, 'projected_surge')
        s_fiscal = get_val(fiscal_df, state, 'total_fiscal_risk')
        
        # Define s_df first
        s_df = df[df['state'] == state]
        s_enrol = s_df['age_0_5'].sum() + s_df['age_5_17'].sum() + s_df['age_18_greater'].sum()
        s_updates = s_df['bio_age_5_17'].sum() + s_df['bio_age_17_'].sum() + s_df['demo_age_5_17'].sum() + s_df['demo_age_17_'].sum()

        # Calculate granular risk components for "Overall" analysis
        s_maint_gap = (s_df['age_5_17'].sum() - s_df['bio_age_5_17'].sum()) / s_df['age_5_17'].sum() if s_df['age_5_17'].sum() > 0 else 0
        s_mig_churn = s_df['demo_age_17_'].sum() / s_df['age_18_greater'].sum() if s_df['age_18_greater'].sum() > 0 else 0
        
        state_stats[state] = {
            'priority_score': float(s_prio),
            'projected_surge': int(s_surge),
            'fiscal_risk': float(s_fiscal),
            'maintenance_gap': float(s_maint_gap),
            'migration_churn': float(s_mig_churn),
            'total_enrollment': int(s_enrol),
            'total_updates': int(s_updates)
        }
        
    output_data['map_data'] = state_stats

    # Write to file
    outfile = os.path.join(OUTPUT_DIR, 'analysis_results.json')
    with open(outfile, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✅ Results saved to {outfile}")
    print("DONE.")

if __name__ == "__main__":
    main()
