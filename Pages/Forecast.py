
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from databricks import sql
import pandas as pd
from datetime import datetime
from statsmodels.tsa.arima.model import ARIMA


def get_flight_data(source,destination,airline):
    connection = sql.connect(server_hostname = "dbc-f8198b57-0dee.cloud.databricks.com",
                 http_path       = "sql/protocolv1/o/5427325314372947/1209-184348-80pwrxb4",
                 access_token    = "dapid625c05398e4533355e51fbec267c8bb")
    query = f"""SELECT id, from, date_from, to, price, 
              airline FROM flight_recommendation.default.flight
              where '{source}' = from 
              and '{destination}'= to and airline = '{airline}'
            """
    result = pd.read_sql(query, connection)
    result['price']=result['price'].astype(float)
    min_prices = result.groupby('date_from')['price'].min().reset_index()
    min_prices['price_diff'] = min_prices['price'] - 2 * min_prices['price'].shift(1) + min_prices['price'].shift(2)
    min_prices = min_prices.dropna()
    return min_prices


def arima_model(data,forecast):

    model = ARIMA(data['price'], order=(4, 1, 7))
    results = model.fit()
    if forecast == 0.0:
      forecast_steps = 10
      predictions = results.get_prediction(start=len(data), end=len(data) + forecast_steps - 1)
      return pd.DataFrame(predictions.predicted_mean)
    else:
      forecast_steps = int(forecast)
      predictions = results.get_prediction(start=len(data), end=len(data) + forecast_steps - 1)
      return pd.DataFrame(predictions.predicted_mean)


def plot_predictions(data, predictions):
    data['data'] = 'historic'
    predictions['data'] = 'forecast'

    last_date = data['date_from'].max()
    last_date = pd.to_datetime(last_date)

    historic_df = data[['date_from', 'price', 'data']]
    forecast_df = pd.DataFrame({
        'date_from': pd.date_range(start=last_date + pd.to_timedelta(1, unit='D'), periods=len(predictions)),
        'predict': predictions.predicted_mean,
        'data': 'forecast'
    })

    df = pd.concat([historic_df, forecast_df], ignore_index=True)

    if df['predict'].empty:
      st.warning("No Data Available")
    else:
      today_date = datetime.today().strftime('%Y-%m-%d')
      df['date_from'] = pd.to_datetime(df['date_from'])
      data = df[df['date_from'] >= today_date]

      fig = px.line(data, x="date_from", y="price")
      fig.add_scatter(x=data["date_from"], y=data["price"], mode="markers",name='Historic')
      fig.add_scatter(x=data["date_from"], y=data["predict"], mode="lines+markers",name='Forecast')
      st.plotly_chart(fig,width = 200)

st.title("Flight Price Forecasting")

source = ["New York, NY (all airports)","Los Angeles, CA (LAX)",
"Chicago, IL (all airports)","Houston, TX (all airports)","Boston, MA (BOS)"]
destination = [
    "Phoenix, AZ (all airports)", "San Diego, CA (SAN)", "Chicago, IL (all airports)",
    "Houston, TX (all airports)", "Los Angeles, CA (LAX)", "New York, NY (all airports)",
    "Columbus, OH (CMH)", "Philadelphia, PA (PHL)", "Charlotte, NC (CLT)",
    "Dallas, TX (all airports)", "San Jose, CA (SJC)", "Jacksonville, FL (JAX)",
    "Indianapolis, IN (IND)", "Austin, TX (AUS)", "San Francisco, CA (SFO)",
    "San Antonio, TX (SAT)", "Fort Worth (DFW)", "Seattle, WA (SEA)",
    "Denver, CO (DEN)"
]

source = st.sidebar.selectbox("Enter the Source City",source)
destination = st.sidebar.selectbox("Enter the Destination City",destination)

airline = ['Spirit','American','United','Delta','JetBlue','Multiple Airlines','Alaska',
           'Frontier','Southwest','Other Airline','Allegiant','Sun Country Airlines',
           'Southern Airways Express']

airline = st.sidebar.selectbox("Select Airline", airline)
data = get_flight_data(source,destination,airline)

forecast = st.number_input("Enter Days To Be Forecasted For :",value=10)

if st.button("Forecast Price"):
  predictions = arima_model(data,forecast)
  plot_predictions(data, predictions)


