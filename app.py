# Import libraries
import plotly
import streamlit as st
import pandas as pd
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from config import URI
import plotly.express as px
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from streamlit_autorefresh import st_autorefresh


# Connect to the Mongo atlas
client = MongoClient(URI, server_api=ServerApi("1"), tls=True, tlsAllowInvalidCertificates=True,  connectTimeoutMS=60000 )

#Select the database
db = client["ecommerce_db"]
collection = db["samsung_timeseries"] # select collection


# Create function to load data
def load_data(collection):
    """Create a pandas dataframe from mongo collection"""
    data = list(collection.find())
    df = pd.DataFrame(data)
    return df

# Create function to get price difference between scraping runs
def get_price_difference(df):
    """Get the price difference between scraping subsequent runs"""
    df = df.sort_values(by=["product", "timestamp"]) # sort by product name & timestamp
    
    latest_entries = df.groupby("product").tail(2) # get details on the 2 most recent runs
    
    # Get details on the previous run
    previous_data = latest_entries.groupby("product").head(1)
    
    # Get details on the current run
    current_data = latest_entries.groupby("product").tail(1)
    
    # Merge the the two above
    comparison_df = pd.merge(previous_data, current_data, on="product", suffixes=("_previous", "_latest"),  how="inner")
    
    # Get the price difference
    comparison_df["price_difference"] = comparison_df["current_price_latest"] - comparison_df["current_price_previous"]
    
    # get the percentage difference
    comparison_df["Price_change"] = (comparison_df["price_difference"] / comparison_df["current_price_latest"]) * 100
    
    # rename columns
    comparison_df.rename({"timestamp_latest": "Updated_at", "current_price_latest": "Price", "product": "Product"}, inplace=True, axis=1)
    
    return comparison_df


# Load the data
df = load_data(collection)


# Call function to get price difference
new_df = get_price_difference(df)


# Set page layout
st.set_page_config(page_title="My App", page_icon=":chart_with_upwards_trend:", layout="wide")

# Define the title 
st.title("📱 Jumia Samsung Price Tracker")

# Define product list
st.write("## Product list")

refresh = st.checkbox("Enable auto-refresh")

if refresh:
    st_autorefresh(interval=4200000, key="conditionalrefresh")

new_df_sorted = new_df[["Updated_at", "Product", "Price", "Price_change" ]].sort_values(by=["Updated_at", "Price_change"], ascending=False).reset_index(drop=True)

# st.dataframe(new_df[["Updated_at", "Product", "Price", "Price_change" ]].sort_values(by=["Updated_at", "Price_change"], ascending=False), width=3000).reset_index(drop=True)

# Define the dataframe
st.dataframe(new_df_sorted, width=3000)

# Define items in  the selectbox
product_name = st.selectbox("🔍 Select product to view price history", new_df["Product"].unique())

st.metric(label=product_name, 
          value=f""" Ksh {new_df.loc[new_df["Product"] == product_name]["Price"].values[0]:,.0f}""", 
          delta=f"price change {round(new_df.loc[new_df["Product"] == product_name]["Price_change"].values[0])}%",
          delta_color="normal",
          label_visibility="hidden")

# Filter data for the selected product
product_df = df.loc[df["product"] == product_name].sort_values(by="timestamp")

# Plot line chart using plotly
st.subheader(f"📈 Price History of {product_name}", divider="rainbow")
fig = px.line(product_df, x="timestamp", y="current_price")#, markers=True
fig.update_layout(xaxis_title="Time",
                  yaxis_title="Price")

st.plotly_chart(fig)





    

    
    
    
    
    
    
    
    
    




