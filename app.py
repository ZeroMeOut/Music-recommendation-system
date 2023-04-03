import pandas as pd
import numpy as np
import pickle
from tqdm import tqdm
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu

import yaml
from yaml.loader import SafeLoader

import difflib

if 'login' not in st.session_state:
    st.session_state.login = True

if 'main' not in st.session_state:
    st.session_state.main = False

if 'user' not in st.session_state:
    st.session_state.user = ''

if 'authentication_status' not in st.session_state:
    st.session_state.authentication_status = None

if 'nav' not in st.session_state:
    st.session_state.nav = None

if 'name' not in st.session_state:
    st.session_state.name = ''

if st.session_state.login:
    selected = option_menu(
        menu_title=None,
        options=["login", "signup"],
        orientation="horizontal"
    )
    st.session_state.nav = selected
else:
    st.session_state.nav = None

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

if st.session_state.nav == "login":
    name, authentication_status, username = authenticator.login('Login', 'main')
    st.session_state.authentication_status = authentication_status
    st.session_state.name = name
    st.session_state.user = username

# st.write(st.session_state.authentication_status)
# st.write(st.session_state.main)

if st.session_state.authentication_status:
    st.session_state.main = True
    st.session_state.login = False
else:
    st.session_state.main = False
    st.session_state.login = True

if st.session_state.main:
    logout = authenticator.logout('Logout', 'sidebar')
    st.write(f'Welcome *{st.session_state.name}*')

    df = pd.read_csv("data.csv")

    df["artists"] = df["artists"].str.replace("[", "")
    df["artists"] = df["artists"].str.replace("]", "")
    df["artists"] = df["artists"].str.replace("'", "")

    tracks = df['name']

    temp = df['id']
    df["song"] = 'https://open.spotify.com/track/' + temp.astype(str)


    def convert(row):
        return '<a href="{}" target="_blank">{}</a>'.format(row['song'], row[12])


    df['song'] = df.apply(convert, axis=1)


    class SpotifyRecommender():
        def __init__(self, rec_data):
            # our class should understand which data to work with
            self.rec_data_ = rec_data

        # if we need to change data
        def change_data(self, rec_data):
            self.rec_data_ = rec_data

        # function which returns recommendations, we can also choose the amount of songs to be recommended
        def get_recommendations(self, song_name, amount=1):
            distances = []
            # choosing the data for our song
            song = self.rec_data_[(self.rec_data_.name.str.lower() == song_name.lower())].head(1).values[0]
            # dropping the data with our song
            res_data = self.rec_data_[self.rec_data_.name.str.lower() != song_name.lower()]
            for r_song in tqdm(res_data.values):
                dist = 0
                for col in np.arange(len(res_data.columns)):
                    # indeces of non-numerical columns
                    if not col in [1, 6, 12, 14, 18, 19]:
                        # calculating the manhettan distances for each numerical feature
                        dist = dist + np.absolute(float(song[col]) - float(r_song[col]))
                distances.append(dist)
            res_data['distance'] = distances
            # sorting our data to be ascending by 'distance' feature
            res_data = res_data.sort_values('distance')
            columns = ['artists', 'song']
            return res_data[columns][:amount]


    recommender = SpotifyRecommender(df)


    def predict_mrs(value, no_of_r):
        st.write(recommender.get_recommendations(value, int(no_of_r)).to_html(escape=False, index=False),
                 unsafe_allow_html=True)


    pickle_out = open("predict_mrs.pkl", "wb")
    pickle.dump(predict_mrs, pickle_out)
    pickle_out.close()

    pickle_in = open('predict_mrs.pkl', 'rb')
    classifier = pickle.load(pickle_in)

    st.title('Music Recommendation System')
    st.subheader('Song Name:')
    song_name = st.text_input('')
    submit = st.button('Predict')


    # Finding the closes match
    def userInput():
        if not song_name.isdigit():
            # Finding the close match for the movie name given by the user
            find_close_match = difflib.get_close_matches(song_name, tracks)
            if not find_close_match:
                close_match = 'Food'
            else:
                close_match = find_close_match[0]
            return close_match


    st.subheader("Recommendations:")

    if submit:
        predict_mrs(userInput(), 10)

    if st.session_state.user == 'admin3519':
        st.subheader("Users info:")
        with open('config.yaml') as file:
            temp = []
            try:
                data = yaml.safe_load(file)
                for key, value in data.items():
                    temp.append(value)
                data2 = (pd.DataFrame(temp[1]))
                st.write(data2)
            except yaml.YAMLError as exception:
                st.write(exception)

    # SIDEBAR
    st.sidebar.title('Observations')
    st.sidebar.write('* It will take 1.2 years for someone to listen to all the songs.')
    st.sidebar.write(
        '* An artist creating a high energy song with either electric instruments or electronic songs has the '
        'bestchance'
        'of getting popular')
    st.sidebar.write(
        '* The most popular artist from 1921–2020 is [*The Beatles*]('
        'https://open.spotify.com/artist/3WrFJ7ztbogyGnTHbHJFl2)')

elif st.session_state.authentication_status is False:
    st.error('Username/password is incorrect')
elif st.session_state.authentication_status is None:
    st.warning('Please enter your username and password')
if st.session_state.nav == "signup":
    try:
        if authenticator.register_user('Register user', preauthorization=False):
            with open('config.yaml', 'w') as file:
                yaml.dump(config, file, default_flow_style=False)
            st.success('User registered successfully')
    except Exception as e:
        st.error(e)
