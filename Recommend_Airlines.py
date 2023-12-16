
import streamlit as st
from databricks import sql
import pandas as pd
import datetime as dt
from st_aggrid import AgGrid


def get_flight_data():
    connection = sql.connect(server_hostname = st.secrets['server_hostname'],
                 http_path       = st.secrets['http_path'],
                 access_token    = st.secrets['access_token'])
    with connection.cursor() as cursor:
      cursor.execute("SELECT * FROM flight_recommendation.default.flight")
      result = cursor.fetchall()
      data = pd.DataFrame(result)
      data.columns = ['id','_c0','to','from','date_to','date_from','pos_overall','url','type','price',
      'airline','duration']
      columns_titles = ['id','from','date_from','to','date_to','url','type','price',
      'airline','duration']
      data_f=data.reindex(columns=columns_titles)
      return data_f

def get_popularity_data():
    connection = sql.connect(server_hostname = st.secrets['server_hostname'],
                 http_path       = st.secrets['http_path'],
                 access_token    = st.secrets['access_token'])
    with connection.cursor() as cursor:
      cursor.execute("SELECT * FROM flight_recommendation.default.flightpopularity")
      result = cursor.fetchall()
      data = pd.DataFrame(result)
      data.columns = ['airline', 'popularity_score']
      return data

def get_user_data():
    connection = sql.connect(server_hostname = st.secrets['server_hostname'],
                 http_path       = st.secrets['http_path'],
                 access_token    = st.secrets['access_token'])
    with connection.cursor() as cursor:
      cursor.execute("SELECT * FROM flight_recommendation.default.user")
      result = cursor.fetchall()
      data = pd.DataFrame(result)
      data.columns = ['userid','name','age','email','phone_number','travel_purpose','flight_id','id']
      return data


def generate_recommendations(price_range, date_range, source, destination, sort_by):

    # Filter flights based on user inputs
    flight_data = get_flight_data()
    popularity_data = get_popularity_data()

    date_mask = (flight_data['date_from'] >= date_range[0]) & (flight_data['date_to'] <= date_range[1])
    source_dest_mask = ((flight_data['from'].str.contains(source)) & (flight_data['to'].str.contains(destination)))

    price_mask = (flight_data['price'].astype(int) >= price_range[0]) & (flight_data['price'].astype(int) <= price_range[1])

    filtered_data = flight_data[date_mask & source_dest_mask & price_mask]

    # Merge with popularity data and sort by popularity
    if not filtered_data.empty:
        filtered_data = pd.merge(filtered_data, popularity_data, how='left', on='airline')
        if sort_by == 'Popularity':
            filtered_data = filtered_data.sort_values(by='popularity_score', ascending=False)
        elif sort_by == 'Price: Lowest':
            filtered_data = filtered_data.sort_values(by='price', ascending=True)
        elif sort_by == 'Price: Highest':
            filtered_data = filtered_data.sort_values(by='price', ascending=False)

    return pd.DataFrame(filtered_data)

def generate_flight_recommendations(user_id, price_range, date_range, source, destination, sort_by, top_k=3):
    # Merge flight and user data

    flight_data = get_flight_data()
    user_data = get_user_data()
    user_data['userid'] = user_data['userid'].astype(int)
    user_data['flight_id'] = user_data['flight_id'].astype(int)

    merged_data = pd.merge(flight_data, user_data, how='left', left_on='id', right_on='flight_id')

    merged_data['userid'] = merged_data['userid'].astype(float).fillna(0)
    merged_data['flight_id'] = merged_data['flight_id'].astype(float).fillna(0)
    merged_data['flight_id'] = merged_data['flight_id'].astype(int)

    # Filter flights for the given user
    user_flights = merged_data[merged_data['userid'] == user_id]

    # Create a user profile based on historical airlines
    user_profile = user_flights.groupby('airline').size().reset_index(name='num_trips')

    # Content-Based Filtering: Recommend flights based on historical airlines
    recommended_airlines = user_flights['airline'].value_counts().index[:top_k].tolist()

    # Get entire flight data for the recommended airlines
    recommended_flights_data = flight_data[flight_data['airline'].isin(recommended_airlines)]

    # Sort recommended flights based on the count of historical flights for each airline
    recommended_flights_data['airline_count'] = recommended_flights_data['airline'].map(user_profile.set_index('airline')['num_trips'])
    recommended_flights_data = recommended_flights_data.sort_values(by='airline_count', ascending=False).drop('airline_count', axis=1)

    if recommended_flights_data.empty:
      date_mask = (recommended_flights_data['date_from'] >= date_range[0]) & (recommended_flights_data['date_to'] <= date_range[1])
      source_dest_mask = ((recommended_flights_data['from'].str.contains(source)) & (recommended_flights_data['to'].str.contains(destination)))

      price_mask = (recommended_flights_data['price'].astype(int) >= price_range[0]) & (recommended_flights_data['price'].astype(int) <= price_range[1])

      filtered_data = recommended_flights_data[date_mask & price_mask & source_dest_mask]
      return pd.DataFrame(filtered_data)
    else:
      # get all flights data
      date_mask = (flight_data['date_from'] >= date_range[0]) & (flight_data['date_to'] <= date_range[1])
      source_dest_mask = ((flight_data['from'].str.contains(source)) & (flight_data['to'].str.contains(destination)))

      price_mask = (flight_data['price'].astype(int) >= price_range[0]) & (flight_data['price'].astype(int) <= price_range[1])

      filtered_data_1 = flight_data[date_mask & price_mask & source_dest_mask]

      # get flights data from present in user history
      date_mask = (recommended_flights_data['date_from'] >= date_range[0]) & (recommended_flights_data['date_to'] <= date_range[1])
      source_dest_mask = ((recommended_flights_data['from'].str.contains(source)) & (recommended_flights_data['to'].str.contains(destination)))

      price_mask = (recommended_flights_data['price'].astype(int) >= price_range[0]) & (recommended_flights_data['price'].astype(int) <= price_range[1])

      filtered_data_2 = recommended_flights_data[date_mask & price_mask & source_dest_mask]

      filtered_data = pd.concat([filtered_data_1, filtered_data_2])
      filtered_data = filtered_data.drop_duplicates(subset=['id'])

      if sort_by == 'Price: Lowest':
          recommendations = filtered_data.sort_values(by='price', ascending=True)
          return pd.DataFrame(recommendations)
      if sort_by == 'Price: Highest':
          recommendations = filtered_data.sort_values(by='price', ascending=False)
          return pd.DataFrame(recommendations)
      else:
        return pd.DataFrame(filtered_data)

st.title('Personalized Flight Recommendation System')

tabs = st.tabs(["New User", "Existing User"])
c1 = tabs[0]
c2 = tabs[1]


with st.sidebar:
    min_price = st.number_input('Enter the price range', min_value=0, max_value=10000, value=0,key='A')
    max_price = st.number_input('Enter the price range', min_value=0, max_value=10000, value=1000,key='B')

    price_range = (min_price, max_price)

    start_date = st.date_input('Start date',key='SD')
    end_date = st.date_input('End date',key='ED')

    date_range = (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))

    source = st.text_input("Enter the Source City",key='src')
    destination = st.text_input("Enter the Destination City",key='dest')

with c1:
  sort_by = st.selectbox("Sort by", ["Popularity", "Price: Lowest", "Price: Highest"],key='S')
  if st.button('Recommend Flights',key='B1'):

    result = generate_recommendations(price_range, date_range, source, destination, sort_by)

    if result.empty:
      st.warning("No flights found")
    else:
      st.write("Recommended flights")
      AgGrid(result)

with c2:
  user_id_to_recommend = st.number_input('Enter the user id', min_value=0, max_value=10000, value=0)

  sort_by = st.selectbox("Sort by", ["Default","Price: Lowest", "Price: Highest"],key='S1')
  if st.button('Recommend Flights',key="B2"):

    result = generate_flight_recommendations(user_id_to_recommend, price_range, date_range, source, destination, sort_by)
    if result.empty:
      st.warning("No flights found")
    else:
      st.write("Recommended flights")
      AgGrid(result)

