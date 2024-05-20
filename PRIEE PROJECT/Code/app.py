import streamlit as st
import pickle
import time
from datetime import datetime, timedelta
import plotly.express as px

# Load the sentiment analysis model
model = pickle.load(open('Twitter_sentiment.pkl', 'rb'))

# Mock relevance detection model function
def mock_relevance_predict(tweet):
    # Simple mock logic for demonstration purposes
    irrelevant_keywords = ["spam", "advertisement", "irrelevant"]
    if any(keyword in tweet.lower() for keyword in irrelevant_keywords):
        return ["Irrelevant"]
    return ["Relevant"]

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'positive_tweet_count' not in st.session_state:
    st.session_state.positive_tweet_count = 0
if 'negative_tweet_count' not in st.session_state:
    st.session_state.negative_tweet_count = 0
if 'lockout_time' not in st.session_state:
    st.session_state.lockout_time = None
if 'age' not in st.session_state:
    st.session_state.age = None
if 'tweets' not in st.session_state:
    st.session_state.tweets = []
if 'registered_users' not in st.session_state:
    st.session_state.registered_users = []

# Define the registration page
def register_page():
    st.title("Register")
    new_email = st.text_input("Email")
    new_password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    age = st.number_input("Age", min_value=1, max_value=100, step=1)
    register_button = st.button("Register")

    if register_button:
        if new_password == confirm_password:
            st.session_state.registered_users.append({
                'email': new_email, 
                'password': new_password, 
                'age': age, 
                'positive_tweet_count': 0, 
                'negative_tweet_count': 0, 
                'tweets': [], 
                'lockout_time': None
            })
            st.success("Registration successful! Please log in.")
        else:
            st.error("Passwords do not match")

# Define the login page
def login_page():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        for user in st.session_state.registered_users:
            if user['email'] == email and user['password'] == password:
                st.success("Login successful!")
                st.session_state.logged_in = True
                st.session_state.age = user['age']
                st.session_state.email = email
                st.session_state.positive_tweet_count = user['positive_tweet_count']
                st.session_state.negative_tweet_count = user['negative_tweet_count']
                st.session_state.tweets = user['tweets']
                st.session_state.lockout_time = user['lockout_time']
                break
        else:
            st.error("Invalid email or password")

# Define the logout functionality
def logout():
    for user in st.session_state.registered_users:
        if user['email'] == st.session_state.email:
            user['positive_tweet_count'] = st.session_state.positive_tweet_count
            user['negative_tweet_count'] = st.session_state.negative_tweet_count
            user['tweets'] = st.session_state.tweets
            user['lockout_time'] = st.session_state.lockout_time
            break

    st.session_state.logged_in = False
    st.session_state.age = None
    st.session_state.email = None
    st.session_state.positive_tweet_count = 0
    st.session_state.negative_tweet_count = 0
    st.session_state.tweets = []
    st.session_state.lockout_time = None
    st.success("Logged out successfully!")

# Define the sentiment analysis functionality
def sentiment_analysis():
    st.title('Twitter Sentiment Analysis')

    # Display profile icon with positive or negative badge if applicable
    st.sidebar.header("Profile")
    st.sidebar.write("Username:", st.session_state.email)
    if st.session_state.positive_tweet_count > 5:
        st.sidebar.success("🌟 Positive Badge 🌟")
    if 5 < st.session_state.negative_tweet_count <= 10:
        st.sidebar.error("🚫 Negative Badge 🚫")

    if st.session_state.lockout_time and datetime.now() < st.session_state.lockout_time:
        st.warning(f"You are temporarily locked out due to posting too many negative tweets. Please try again after {st.session_state.lockout_time.strftime('%Y-%m-%d %H:%M:%S')}.")
        return

    tweet = st.text_input('Enter your tweet')
    submit = st.button('Predict')

    if submit:
        start = time.time()
        sentiment_prediction = model.predict([tweet])
        relevance_prediction = mock_relevance_predict(tweet)
        end = time.time()

        st.write('Prediction time taken:', round(end - start, 2), 'seconds')
        sentiment = sentiment_prediction[0]
        relevance = relevance_prediction[0]

        if st.session_state.age is not None and st.session_state.age < 18 and sentiment != "Positive":
            st.warning("As you are under 18, you can only post positive tweets.")
        elif sentiment == "Negative" and relevance == "Irrelevant":
            st.warning("Negative and irrelevant tweets cannot be posted.")
        else:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            st.session_state.tweets.append((tweet, timestamp))
            st.write("Tweet posted successfully.")
            if sentiment == "Positive":
                st.session_state.positive_tweet_count += 1
                st.success("Your tweet is positive.")
            elif sentiment == "Negative":
                st.session_state.negative_tweet_count += 1
                st.warning("Your tweet is negative.")
                if st.session_state.negative_tweet_count == 5:
                    st.warning("You have posted 5 negative tweets. One more negative tweet will restrict you from posting for 6 hours.")
                elif st.session_state.negative_tweet_count > 5:
                    st.error("You have posted too many negative tweets. You are now restricted from posting for 6 hours.")
                    st.session_state.lockout_time = datetime.now() + timedelta(hours=6)
            display_tweets()
            display_pie_chart()

# Define the function to display tweets with time and date
def display_tweets():
    st.subheader("Posted Tweets")
    for tweet, timestamp in st.session_state.tweets:
        st.write(f"{timestamp} - {tweet}")

# Define the function to display a pie chart of sentiments
def display_pie_chart():
    sentiments = [model.predict([tweet[0]])[0] for tweet in st.session_state.tweets]
    sentiment_counts = {sentiment: sentiments.count(sentiment) for sentiment in set(sentiments)}
    fig = px.pie(names=list(sentiment_counts.keys()), values=list(sentiment_counts.values()), title='Sentiment Distribution of Tweets')
    st.plotly_chart(fig)

# Render appropriate page based on authentication status
if not st.session_state.logged_in:
    if not st.session_state.registered_users:
        register_page()
    else:
        login_page()
else:
    st.button("Logout", on_click=logout)
    sentiment_analysis()
