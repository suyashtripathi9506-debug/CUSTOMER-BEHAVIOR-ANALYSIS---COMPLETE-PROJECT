# ================================================================
# CUSTOMER BEHAVIOR ANALYSIS - TUTORIAL & EXAMPLES
# ================================================================

"""
This file contains step-by-step examples showing how to use and customize
the Customer Behavior Analysis project.
"""

import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta

print("\n" + "="*70)
print("CUSTOMER BEHAVIOR ANALYSIS - TUTORIAL & EXAMPLES")
print("="*70)

# ========== PART 1: BASIC PANDAS OPERATIONS ==========
print("\n\n📚 PART 1: BASIC PANDAS OPERATIONS")
print("="*70)

# Example 1: Loading data
print("\n[Example 1.1] Loading customer data from CSV")
df = pd.read_csv('customer_behavior_for_powerbi.csv')
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")

# Example 2: Basic statistics
print("\n[Example 1.2] Basic statistics")
print(df[['total_spent', 'purchase_frequency', 'engagement_score']].describe())

# Example 3: Value counts
print("\n[Example 1.3] Customer distribution by segment")
print(df['customer_segment'].value_counts())

# Example 4: Filtering
print("\n[Example 1.4] Filter high-value customers (>₹100k)")
high_value = df[df['total_spent'] > 100000]
print(f"Found {len(high_value)} high-value customers")
print(high_value[['customer_name', 'total_spent', 'churn_risk']].head())

# ========== PART 2: DATA AGGREGATION (Pandas) ==========
print("\n\n📊 PART 2: DATA AGGREGATION")
print("="*70)

# Example 5: GroupBy operations
print("\n[Example 2.1] Revenue by customer segment")
segment_summary = df.groupby('customer_segment').agg({
    'customer_id': 'count',
    'total_spent': ['sum', 'mean', 'median']
}).round(2)
print(segment_summary)

# Example 6: Pivot tables
print("\n[Example 2.2] Cross-tabulation: Segment vs Churn Risk")
pivot = pd.pivot_table(df, values='total_spent', index='customer_segment', 
                        columns='churn_risk', aggfunc='sum')
print(pivot)

# Example 7: Sorting
print("\n[Example 2.3] Top 10 customers by CLV")
top_10 = df.nlargest(10, 'clv_estimate')[['customer_name', 'total_spent', 'clv_estimate']]
print(top_10)

# ========== PART 3: NUMPY OPERATIONS ==========
print("\n\n🔢 PART 3: NUMPY OPERATIONS")
print("="*70)

# Example 8: Array operations
print("\n[Example 3.1] Calculate percentiles for spending")
spending = df['total_spent'].values
p25 = np.percentile(spending, 25)
p50 = np.percentile(spending, 50)
p75 = np.percentile(spending, 75)
print(f"25th percentile: ₹{p25:,.0f}")
print(f"50th percentile (median): ₹{p50:,.0f}")
print(f"75th percentile: ₹{p75:,.0f}")

# Example 9: Conditional operations (np.where & np.select)
print("\n[Example 3.2] Create spending categories using NumPy")
spending_category = np.select(
    [df['total_spent'] > 200000, df['total_spent'] > 100000, df['total_spent'] > 50000],
    ['Premium', 'Gold', 'Silver'],
    default='Bronze'
)
df['spending_category'] = spending_category
print(pd.Series(spending_category).value_counts())

# Example 10: Statistical analysis
print("\n[Example 3.3] Statistical comparison of segments")
loyal_customers = df[df['customer_segment'] == 'Loyal']['total_spent']
atrisk_customers = df[df['customer_segment'] == 'At-Risk']['total_spent']
print(f"Loyal customers avg spend: ₹{loyal_customers.mean():,.0f}")
print(f"At-Risk customers avg spend: ₹{atrisk_customers.mean():,.0f}")
print(f"Difference: ₹{loyal_customers.mean() - atrisk_customers.mean():,.0f}")

# ========== PART 4: SQL OPERATIONS ==========
print("\n\n🗄️  PART 4: SQL OPERATIONS")
print("="*70)

# Example 11: Running SQL queries
print("\n[Example 4.1] Query customer transactions")
conn = sqlite3.connect('customer_behavior.db')
cursor = conn.cursor()

query = """
SELECT customer_segment, COUNT(*) as customer_count, 
       ROUND(AVG(amount), 2) as avg_spending
FROM (
    SELECT c.customer_segment, SUM(t.amount) as amount
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    GROUP BY c.customer_id
)
GROUP BY customer_segment
ORDER BY avg_spending DESC
"""

result = pd.read_sql_query(query, conn)
print(result)

# Example 12: Custom SQL analysis
print("\n[Example 4.2] Find customers who haven't purchased in 6 months")
churn_risk_query = """
SELECT c.customer_id, c.customer_name, 
       CAST((julianday('now') - julianday(MAX(t.transaction_date))) AS INTEGER) as days_inactive
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id
HAVING days_inactive > 180
LIMIT 10
"""
churn_risk_df = pd.read_sql_query(churn_risk_query, conn)
print(f"Found {len(churn_risk_df)} customers at high churn risk")
print(churn_risk_df.head())

conn.close()

# ========== PART 5: CUSTOM ANALYTICS ==========
print("\n\n🎯 PART 5: CUSTOM ANALYTICS")
print("="*70)

# Example 13: RFM Segmentation
print("\n[Example 5.1] Create RFM segments")
df['R_score'] = pd.qcut(df['days_since_last_purchase'], q=5, labels=[5,4,3,2,1], duplicates='drop')
df['F_score'] = pd.qcut(df['purchase_frequency'].rank(method='first'), q=5, labels=[1,2,3,4,5], duplicates='drop')
df['M_score'] = pd.qcut(df['total_spent'], q=5, labels=[1,2,3,4,5], duplicates='drop')
df['RFM_Score'] = df['R_score'].astype(str) + df['F_score'].astype(str) + df['M_score'].astype(str)
print(df[['customer_name', 'R_score', 'F_score', 'M_score', 'RFM_Score']].head(10))

# Example 14: Customer health score
print("\n[Example 5.2] Calculate customer health score")
df['health_score'] = (
    (df['engagement_score'] / 100 * 0.3) +
    (1 - (df['days_since_last_purchase'] / df['days_since_last_purchase'].max()) * 0.4) +
    ((df['purchase_frequency'] / df['purchase_frequency'].max()) * 0.3)
) * 100
df['health_score'] = df['health_score'].round(2)
print("Customer Health Scores:")
print(df[['customer_name', 'health_score']].nlargest(10, 'health_score'))

# Example 15: Churn prediction signals
print("\n[Example 5.3] Identify churn warning signals")
churn_signals = df[
    (df['days_since_last_purchase'] > 60) &
    (df['engagement_score'] < 50) &
    (df['purchase_frequency'] < 1)
][['customer_name', 'total_spent', 'days_since_last_purchase', 'engagement_score']]
print(f"Found {len(churn_signals)} customers with churn warnings")
print(churn_signals.head())

# ========== PART 6: BUSINESS INSIGHTS ==========
print("\n\n💡 PART 6: BUSINESS INSIGHTS")
print("="*70)

# Example 16: Customer value distribution
print("\n[Example 6.1] Pareto Analysis (80/20 rule)")
df_sorted = df.sort_values('total_spent', ascending=False)
df_sorted['cumulative_revenue'] = df_sorted['total_spent'].cumsum()
df_sorted['cumulative_pct'] = 100 * df_sorted['cumulative_revenue'] / df_sorted['total_spent'].sum()
top_20_pct = len(df) * 0.2
revenue_from_top_20 = df_sorted.head(int(top_20_pct))['total_spent'].sum()
total_revenue = df['total_spent'].sum()
print(f"Top 20% of customers generate {100 * revenue_from_top_20 / total_revenue:.1f}% of revenue")

# Example 17: Channel ROI analysis
print("\n[Example 6.2] Channel effectiveness")
channel_analysis = df.groupby('acquisition_channel').agg({
    'customer_id': 'count',
    'total_spent': ['sum', 'mean'],
    'engagement_score': 'mean',
    'churn_risk': lambda x: (x == 'Critical').sum()
}).round(2)
print(channel_analysis)

# Example 18: Retention metrics
print("\n[Example 6.3] Calculate retention by tenure")
df['tenure_band'] = pd.cut(df['tenure_months'], bins=[0, 3, 6, 12, 24, 100])
retention = df.groupby('tenure_band', observed=True).agg({
    'customer_id': 'count',
    'total_spent': 'mean',
    'churn_risk': lambda x: (x == 'Critical').sum() / len(x) * 100
}).round(2)
retention.columns = ['customers', 'avg_spent', 'critical_risk_pct']
print(retention)

# ========== PART 7: EXPORT & REPORTING ==========
print("\n\n📄 PART 7: EXPORT & REPORTING")
print("="*70)

# Example 19: Create custom Excel report
print("\n[Example 7.1] Create custom multi-sheet Excel report")
with pd.ExcelWriter('custom_analysis_report.xlsx', engine='openpyxl') as writer:
    # Sheet 1: Summary
    summary_df = pd.DataFrame({
        'Metric': ['Total Customers', 'Total Revenue', 'Avg Customer Value', 'Critical Risk'],
        'Value': [len(df), f"₹{df['total_spent'].sum():,.0f}", 
                 f"₹{df['total_spent'].mean():,.0f}",
                 f"{(df['churn_risk'] == 'Critical').sum()}"]
    })
    summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    # Sheet 2: Top customers
    top_customers = df.nlargest(20, 'total_spent')[
        ['customer_name', 'customer_segment', 'total_spent', 'clv_estimate', 'churn_risk']
    ]
    top_customers.to_excel(writer, sheet_name='Top Customers', index=False)
    
    # Sheet 3: At-risk customers
    at_risk = df[df['churn_risk'].isin(['High', 'Critical'])][
        ['customer_name', 'total_spent', 'days_since_last_purchase', 'engagement_score']
    ]
    at_risk.to_excel(writer, sheet_name='At Risk Customers', index=False)
    
    # Sheet 4: Segment analysis
    segment_data = df.groupby('customer_segment').agg({
        'customer_id': 'count',
        'total_spent': ['sum', 'mean'],
        'engagement_score': 'mean'
    }).round(2)
    segment_data.to_excel(writer, sheet_name='Segment Analysis')

print("✅ Exported: custom_analysis_report.xlsx")

# Example 20: Export for Power BI
print("\n[Example 7.2] Prepare data for Power BI")
powerbi_export = df[[
    'customer_id', 'customer_name', 'country', 'customer_segment',
    'acquisition_channel', 'total_transactions', 'total_spent',
    'purchase_frequency', 'engagement_score', 'clv_estimate',
    'churn_risk', 'value_segment'
]].copy()
powerbi_export.to_csv('powerbi_export.csv', index=False)
print("✅ Exported: powerbi_export.csv (ready for Power BI)")

# ========== PART 8: VISUALIZATION SETUP ==========
print("\n\n📊 PART 8: VISUALIZATION SETUP")
print("="*70)

print("""
[Example 8.1] How to create Matplotlib charts

import matplotlib.pyplot as plt

# Create a figure
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# 1. Bar chart - Revenue by segment
df.groupby('customer_segment')['total_spent'].sum().plot(
    kind='bar', ax=axes[0, 0], color='steelblue', edgecolor='black')
axes[0, 0].set_title('Revenue by Segment')

# 2. Pie chart - Churn distribution
df['churn_risk'].value_counts().plot(
    kind='pie', ax=axes[0, 1], autopct='%1.1f%%')
axes[0, 1].set_title('Churn Risk Distribution')

# 3. Scatter - Spending vs Frequency
axes[1, 0].scatter(df['purchase_frequency'], df['total_spent'],
                   c=df['engagement_score'], cmap='viridis', s=100)
axes[1, 0].set_xlabel('Purchase Frequency')
axes[1, 0].set_ylabel('Total Spent')

# 4. Box plot - CLV by segment
df.boxplot(column='clv_estimate', by='customer_segment', ax=axes[1, 1])

plt.tight_layout()
plt.savefig('custom_dashboard.png', dpi=300, bbox_inches='tight')
plt.show()
""")

# ========== FINAL SUMMARY ==========
print("\n\n" + "="*70)
print("TUTORIAL COMPLETED")
print("="*70)
print("""
You now know how to:
✅ Load and explore customer data with Pandas
✅ Perform aggregations and groupby operations
✅ Use NumPy for statistical analysis
✅ Write SQL queries for complex analysis
✅ Create custom metrics and segments
✅ Export data to Excel and CSV for Power BI
✅ Generate business insights from raw data

Next steps:
1. Modify the queries to match your data structure
2. Create additional custom segments for your use case
3. Export data to Power BI for interactive dashboards
4. Set up automated reporting using Excel/Power BI
5. Create alerts for churn-risk customers
""")
