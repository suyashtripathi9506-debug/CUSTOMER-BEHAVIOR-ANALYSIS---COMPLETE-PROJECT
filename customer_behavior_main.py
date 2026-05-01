# ================================================================
# CUSTOMER BEHAVIOR ANALYSIS - COMPLETE PROJECT
# ================================================================
# Technologies: Python, SQL, Pandas, NumPy, Matplotlib, Excel, Power BI
# ================================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime, timedelta

# ========== 1. DATABASE SETUP (SQL) ==========
def create_database():
    """Create SQLite database with customer tables"""
    conn = sqlite3.connect('customer_behavior.db')
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY,
        customer_name TEXT,
        email TEXT,
        signup_date TEXT,
        country TEXT,
        customer_segment TEXT,
        acquisition_channel TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        transaction_date TEXT,
        product_category TEXT,
        amount REAL,
        quantity INTEGER,
        payment_method TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS engagement (
        engagement_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        engagement_date TEXT,
        page_views INTEGER,
        session_duration_minutes INTEGER,
        items_added_to_cart INTEGER,
        items_purchased INTEGER,
        device_type TEXT)''')
    
    conn.commit()
    return conn, cursor

# ========== 2. INSERT SAMPLE DATA ==========
def insert_sample_data(cursor, conn):
    """Generate realistic customer data using NumPy"""
    np.random.seed(42)
    
    countries = ['India', 'USA', 'UK', 'Germany', 'France', 'Canada', 'Australia']
    segments = ['Loyal', 'At-Risk', 'New', 'Premium', 'Occasional']
    channels = ['Organic Search', 'Social Media', 'Email', 'Referral', 'Paid Ads']
    
    # 200 customers
    customers = [(i, f'Customer_{i}', f'customer{i}@email.com',
                 (datetime.now() - timedelta(days=np.random.randint(30, 730))).strftime('%Y-%m-%d'),
                 np.random.choice(countries),
                 np.random.choice(segments),
                 np.random.choice(channels)) for i in range(1, 201)]
    
    cursor.executemany('INSERT OR IGNORE INTO customers VALUES (?, ?, ?, ?, ?, ?, ?)', customers)
    
    # 1500 transactions
    transactions = [(i, np.random.randint(1, 201),
                    (datetime.now() - timedelta(days=np.random.randint(0, 365))).strftime('%Y-%m-%d'),
                    np.random.choice(['Electronics', 'Accessories', 'Home']),
                    np.random.uniform(20, 1500),
                    np.random.randint(1, 5),
                    np.random.choice(['Credit Card', 'Debit Card', 'PayPal']))
                   for i in range(1, 1501)]
    
    cursor.executemany('INSERT OR IGNORE INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?)', transactions)
    
    # 3000 engagement records
    engagement = []
    eng_id = 1
    for cust_id in range(1, 201):
        for _ in range(15):
            engagement.append((eng_id, cust_id,
                             (datetime.now() - timedelta(days=np.random.randint(0, 60))).strftime('%Y-%m-%d'),
                             np.random.randint(1, 50),
                             np.random.randint(2, 120),
                             np.random.randint(0, 8),
                             np.random.randint(0, 4),
                             np.random.choice(['Mobile', 'Desktop', 'Tablet'])))
            eng_id += 1
    
    cursor.executemany('INSERT OR IGNORE INTO engagement VALUES (?, ?, ?, ?, ?, ?, ?, ?)', engagement)
    conn.commit()
    print("✅ Sample data inserted: 200 customers, 1500 transactions, 3000 engagement records")

# ========== 3. EXTRACT DATA (SQL) ==========
def extract_data(cursor):
    """Extract customer data with SQL JOINs"""
    query = '''SELECT c.customer_id, c.customer_name, c.signup_date, c.country, 
                      c.customer_segment, c.acquisition_channel,
                      COUNT(DISTINCT t.transaction_id) as total_transactions,
                      SUM(t.amount) as total_spent,
                      AVG(t.amount) as avg_transaction_value,
                      SUM(t.quantity) as total_items,
                      MAX(t.transaction_date) as last_purchase_date,
                      COUNT(DISTINCT e.engagement_date) as engagement_days,
                      AVG(e.page_views) as avg_page_views,
                      SUM(e.items_added_to_cart) as total_cart_adds,
                      SUM(CASE WHEN e.items_purchased > 0 THEN 1 ELSE 0 END) as days_with_purchase
               FROM customers c
               LEFT JOIN transactions t ON c.customer_id = t.customer_id
               LEFT JOIN engagement e ON c.customer_id = e.customer_id
               GROUP BY c.customer_id'''
    
    df = pd.read_sql_query(query, sqlite3.connect('customer_behavior.db'))
    return df

# ========== 4. PROCESS DATA (Pandas & NumPy) ==========
def process_metrics(df):
    """Calculate customer metrics using Pandas and NumPy"""
    
    df = df.fillna(0)
    df['signup_date'] = pd.to_datetime(df['signup_date'])
    df['last_purchase_date'] = pd.to_datetime(df['last_purchase_date'], errors='coerce')
    
    # Key metrics
    df['days_since_signup'] = (datetime.now() - df['signup_date']).dt.days
    df['days_since_last_purchase'] = (datetime.now() - df['last_purchase_date']).dt.days.fillna(999)
    df['tenure_months'] = df['days_since_signup'] / 30
    df['purchase_frequency'] = df['total_transactions'] / np.maximum(df['tenure_months'], 1)
    df['avg_order_value'] = df['total_spent'] / np.maximum(df['total_transactions'], 1)
    df['conversion_rate'] = (df['days_with_purchase'] / np.maximum(df['engagement_days'], 1) * 100).fillna(0)
    df['engagement_score'] = np.clip((df['avg_page_views'] / 50) * (df['conversion_rate'] / 100) * 100, 0, 100)
    df['clv_estimate'] = df['avg_order_value'] * df['purchase_frequency'] * 12 * 3
    
    # Churn risk
    df['churn_risk'] = np.select(
        [(df['days_since_last_purchase'] < 30) & (df['purchase_frequency'] > 2),
         (df['days_since_last_purchase'] < 90) & (df['purchase_frequency'] > 1),
         (df['days_since_last_purchase'] < 180),
         (df['days_since_last_purchase'] >= 180)],
        ['Low', 'Medium', 'High', 'Critical'],
        default='Unknown')
    
    # Value segment
    avg_spent = df['total_spent'].mean()
    avg_freq = df['purchase_frequency'].mean()
    df['value_segment'] = np.select(
        [(df['total_spent'] > avg_spent) & (df['purchase_frequency'] > avg_freq),
         (df['total_spent'] > avg_spent),
         (df['purchase_frequency'] > avg_freq)],
        ['Star Customer', 'Big Spender', 'Frequent Buyer'],
        default='Development')
    
    return df

# ========== 5. GENERATE REPORTS (Pandas) ==========
def generate_reports(df):
    """Generate analytical reports"""
    reports = {}
    reports['segment_analysis'] = df.groupby('customer_segment').agg({
        'customer_id': 'count', 'total_spent': ['sum', 'mean'],
        'purchase_frequency': 'mean', 'engagement_score': 'mean'}).round(2)
    reports['churn_risk'] = df.groupby('churn_risk').agg({
        'customer_id': 'count', 'total_spent': 'mean', 'engagement_score': 'mean'}).round(2)
    reports['value_segment'] = df.groupby('value_segment').agg({
        'customer_id': 'count', 'total_spent': ['sum', 'mean'],
        'purchase_frequency': 'mean'}).round(2)
    reports['channel'] = df.groupby('acquisition_channel').agg({
        'customer_id': 'count', 'total_spent': ['sum', 'mean'],
        'engagement_score': 'mean'}).round(2)
    return reports

# ========== 6. EXPORT TO EXCEL ==========
def export_excel(df, reports, filename='Customer_Behavior_Analysis.xlsx'):
    """Export to Excel with multiple sheets"""
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Customer Data', index=False)
        for name, report in reports.items():
            report.to_excel(writer, sheet_name=name.title()[:31])
        summary = pd.DataFrame({
            'Metric': ['Total Customers', 'Total Revenue', 'Avg Customer Value', 
                      'Avg Engagement Score', 'Critical Risk Count'],
            'Value': [len(df), f"₹{df['total_spent'].sum():,.0f}",
                     f"₹{df['total_spent'].mean():,.0f}",
                     f"{df['engagement_score'].mean():.1f}",
                     len(df[df['churn_risk'] == 'Critical'])]})
        summary.to_excel(writer, sheet_name='Executive Summary', index=False)
    print(f"✅ Exported: {filename}")

# ========== 7. CREATE VISUALIZATIONS (Matplotlib) ==========
def create_dashboard(df):
    """Create 9-chart dashboard"""
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. Segment Distribution
    ax1 = fig.add_subplot(gs[0, 0])
    df['customer_segment'].value_counts().plot(kind='bar', ax=ax1, color='steelblue', edgecolor='black')
    ax1.set_title('Customers by Segment', fontweight='bold')
    ax1.set_ylabel('Count')
    
    # 2. Churn Risk Pie
    ax2 = fig.add_subplot(gs[0, 1])
    colors = {'Low': 'green', 'Medium': 'yellow', 'High': 'orange', 'Critical': 'red'}
    df['churn_risk'].value_counts().plot(kind='pie', ax=ax2, autopct='%1.1f%%',
                                         colors=[colors.get(x, 'gray') for x in df['churn_risk'].unique()])
    ax2.set_title('Churn Risk Distribution', fontweight='bold')
    ax2.set_ylabel('')
    
    # 3. Value Segment
    ax3 = fig.add_subplot(gs[0, 2])
    df['value_segment'].value_counts().plot(kind='bar', ax=ax3, color='coral', edgecolor='black')
    ax3.set_title('Value Segmentation', fontweight='bold')
    
    # 4. Spent vs Frequency Scatter
    ax4 = fig.add_subplot(gs[1, 0])
    scatter = ax4.scatter(df['purchase_frequency'], df['total_spent'], 
                         c=df['engagement_score'], cmap='viridis', s=100, alpha=0.6)
    ax4.set_xlabel('Purchase Frequency')
    ax4.set_ylabel('Total Spent (₹)')
    ax4.set_title('Spending vs Frequency', fontweight='bold')
    plt.colorbar(scatter, ax=ax4, label='Engagement')
    
    # 5. Recency Distribution
    ax5 = fig.add_subplot(gs[1, 1])
    recent_df = df[df['days_since_last_purchase'] < 365]
    ax5.hist(recent_df['days_since_last_purchase'], bins=30, color='skyblue', edgecolor='black')
    ax5.set_xlabel('Days Since Last Purchase')
    ax5.set_ylabel('Count')
    ax5.set_title('Recency Distribution', fontweight='bold')
    
    # 6. Engagement by Segment
    ax6 = fig.add_subplot(gs[1, 2])
    df.groupby('customer_segment')['engagement_score'].mean().sort_values(ascending=False).plot(
        kind='barh', ax=ax6, color='lightgreen', edgecolor='black')
    ax6.set_xlabel('Avg Engagement Score')
    ax6.set_title('Engagement by Segment', fontweight='bold')
    
    # 7. CLV by Segment
    ax7 = fig.add_subplot(gs[2, 0])
    clv_data = [df[df['customer_segment'] == seg]['clv_estimate'].values 
                for seg in df['customer_segment'].unique()]
    ax7.boxplot(clv_data, labels=df['customer_segment'].unique())
    ax7.set_ylabel('CLV (₹)')
    ax7.set_title('CLV Distribution by Segment', fontweight='bold')
    
    # 8. Conversion by Channel
    ax8 = fig.add_subplot(gs[2, 1])
    df.groupby('acquisition_channel')['conversion_rate'].mean().sort_values(ascending=False).plot(
        kind='bar', ax=ax8, color='purple', edgecolor='black', alpha=0.7)
    ax8.set_ylabel('Conversion Rate (%)')
    ax8.set_title('Conversion by Acquisition Channel', fontweight='bold')
    ax8.tick_params(axis='x', rotation=45)
    
    # 9. Transaction Count Distribution
    ax9 = fig.add_subplot(gs[2, 2])
    ax9.hist(df['total_transactions'], bins=20, color='orange', edgecolor='black', alpha=0.7)
    ax9.set_xlabel('Number of Transactions')
    ax9.set_ylabel('Number of Customers')
    ax9.set_title('Transaction Distribution', fontweight='bold')
    
    plt.suptitle('Customer Behavior Analysis Dashboard', fontsize=16, fontweight='bold')
    plt.savefig('Customer_Behavior_Dashboard.png', dpi=300, bbox_inches='tight')
    print("✅ Dashboard saved: Customer_Behavior_Dashboard.png")
    plt.show()

# ========== 8. POWER BI EXPORT ==========
def export_powerbi(df):
    """Export clean data for Power BI"""
    powerbi_cols = ['customer_id', 'customer_name', 'country', 'customer_segment',
                   'acquisition_channel', 'total_transactions', 'total_spent', 'purchase_frequency',
                   'days_since_last_purchase', 'engagement_score', 'clv_estimate',
                   'churn_risk', 'value_segment', 'conversion_rate', 'tenure_months']
    
    df[powerbi_cols].to_csv('customer_behavior_for_powerbi.csv', index=False)
    df[powerbi_cols].to_excel('customer_behavior_for_powerbi.xlsx', index=False)
    print("✅ Power BI files: customer_behavior_for_powerbi.csv & .xlsx")

# ========== MAIN ==========
def main():
    print("\n" + "="*70)
    print("CUSTOMER BEHAVIOR ANALYSIS - COMPLETE PIPELINE")
    print("="*70)
    
    print("\n[1/7] Creating database...")
    conn, cursor = create_database()
    insert_sample_data(cursor, conn)
    
    print("[2/7] Extracting data from database...")
    df = extract_data(cursor)
    print(f"✅ Extracted {len(df)} customer records")
    
    print("[3/7] Processing metrics (Pandas + NumPy)...")
    df = process_metrics(df)
    
    print("[4/7] Generating reports...")
    reports = generate_reports(df)
    print("✅ Generated 4 analytical reports")
    
    print("[5/7] Exporting to Excel...")
    export_excel(df, reports)
    
    print("[6/7] Creating visualizations...")
    create_dashboard(df)
    
    print("[7/7] Preparing Power BI data...")
    export_powerbi(df)
    
    print("\n" + "="*70)
    print("📊 KEY STATISTICS")
    print("="*70)
    print(f"Total Customers: {len(df)}")
    print(f"Total Revenue: ₹{df['total_spent'].sum():,.0f}")
    print(f"Avg Customer Value: ₹{df['total_spent'].mean():,.0f}")
    print(f"Avg Purchase Frequency: {df['purchase_frequency'].mean():.2f} per month")
    print(f"Avg Engagement Score: {df['engagement_score'].mean():.1f}/100")
    print(f"Critical Risk Customers: {len(df[df['churn_risk'] == 'Critical'])}")
    print(f"Star Customers: {len(df[df['value_segment'] == 'Star Customer'])}")
    print("="*70)
    
    conn.close()

if __name__ == '__main__':
    main()
