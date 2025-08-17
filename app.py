# app.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from datetime import datetime

# -------------------------
# Load Data
# -------------------------
st.title("Customer Segmentation Dashboard")

df = pd.read_excel("data/raw/Online_Retail.xlsx")
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
df['TotalPrice'] = df['Quantity'] * df['UnitPrice']
df = df[df['CustomerID'].notnull()]

# Reference date for recency calculation
reference_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)

# -------------------------
# Filters
# -------------------------
st.sidebar.header("Filters")

# Country filter
countries = df['Country'].unique().tolist()
selected_countries = st.sidebar.multiselect("Select Countries:", countries, default=countries)

# Date filter
min_date = df['InvoiceDate'].min()
max_date = df['InvoiceDate'].max()
date_range = st.sidebar.date_input("Select Date Range:", [min_date, max_date], min_value=min_date, max_value=max_date)

# Apply filters
filtered_df = df[(df['Country'].isin(selected_countries)) &
                 (df['InvoiceDate'] >= pd.to_datetime(date_range[0])) &
                 (df['InvoiceDate'] <= pd.to_datetime(date_range[1]))]

# -------------------------
# Build RFM Table
# -------------------------
rfm = filtered_df.groupby('CustomerID').agg({
    'InvoiceDate': lambda x: (reference_date - x.max()).days,
    'InvoiceNo': 'nunique',
    'TotalPrice': 'sum'
})
rfm.rename(columns={
    'InvoiceDate': 'Recency',
    'InvoiceNo': 'Frequency',
    'TotalPrice': 'Monetary'
}, inplace=True)

# -------------------------
# RFM Scoring
# -------------------------
rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[4,3,2,1])
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1,2,3,4])
rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1,2,3,4])
rfm['RFM_Score'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)

# -------------------------
# Segmentation
# -------------------------
def segment_me(row):
    if row['R_Score'] >= 3 and row['F_Score'] >= 3:
        return "Champions"
    elif row['R_Score'] >= 3 and row['F_Score'] < 3:
        return "Potential Loyalist"
    elif row['R_Score'] < 3 and row['F_Score'] >= 3:
        return "Loyal Customers"
    elif row['R_Score'] < 3 and row['F_Score'] < 3:
        return "At Risk"
    else:
        return "Others"

rfm['Segment'] = rfm.apply(segment_me, axis=1)

# Segment filter
segments = rfm['Segment'].unique().tolist()
selected_segments = st.sidebar.multiselect("Select Segments:", segments, default=segments)
rfm = rfm[rfm['Segment'].isin(selected_segments)]

# -------------------------
# Display RFM Table
# -------------------------
st.subheader("RFM Table")
st.dataframe(rfm.reset_index())

# -------------------------
# RFM Charts
# -------------------------
st.subheader("RFM Distribution Charts")

fig, axs = plt.subplots(2, 2, figsize=(14,10))

# Recency
sns.histplot(rfm['Recency'], bins=30, kde=True, ax=axs[0,0])
axs[0,0].set_title('Recency Distribution')

# Frequency
sns.histplot(rfm['Frequency'], bins=30, kde=True, ax=axs[0,1])
axs[0,1].set_title('Frequency Distribution')

# Monetary
sns.histplot(rfm['Monetary'], bins=30, kde=True, ax=axs[1,0])
axs[1,0].set_title('Monetary Distribution')

# Segment counts
rfm['Segment'].value_counts().plot(kind='bar', ax=axs[1,1])
axs[1,1].set_title('Customer Segments')

plt.tight_layout()
st.pyplot(fig)

# -------------------------
# Additional Charts
# -------------------------
st.subheader("Top Countries by Sales")
country_sales = filtered_df.groupby("Country")["TotalPrice"].sum().sort_values(ascending=False).head(10)
fig2, ax2 = plt.subplots()
country_sales.plot(kind='bar', ax=ax2, color='skyblue')
ax2.set_ylabel("Total Sales")
ax2.set_title("Top 10 Countries by Sales")
st.pyplot(fig2)

st.subheader("Top 10 Customers by Monetary Value")
top_customers = rfm.sort_values('Monetary', ascending=False).head(10)
fig3, ax3 = plt.subplots()
ax3.bar(top_customers.index.astype(str), top_customers['Monetary'], color='orange')
ax3.set_ylabel("Monetary Value")
ax3.set_title("Top 10 Customers")
plt.xticks(rotation=45)
st.pyplot(fig3)
