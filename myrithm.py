import requests
from bs4 import BeautifulSoup
from langchain.chat_models import ChatOpenAI
import streamlit as st

api_key = 'secret'

def get_page_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as err:
        print(f'Error occurred: {err}')
        return None

def parse_article_links(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all('a')
    links_dict = {
        link.string.strip(): f'https://lite.cnn.com{link.get("href")}'
        for link in links if link.string
    }
    return links_dict

def get_article_text(url):
    html_content = get_page_content(url)
    if not html_content:
        return None

    soup = BeautifulSoup(html_content, 'html.parser')
    paragraphs = soup.find_all('p', class_='paragraph--lite')
    return ' '.join(p.get_text() for p in paragraphs)

def get_articles_list():
    url = "https://lite.cnn.com/"
    html_content = get_page_content(url)
    if not html_content:
        return []

    articles_dict = parse_article_links(html_content)
    articles = list(articles_dict.keys())
    # first link and last 5 links are irrelevent
    relevant_articles = articles[1:-5]

    return [(i+1, name, articles_dict[name]) for i, name in enumerate(relevant_articles)]

def rank_articles(articles_list, llm, user_input):
    ranked_articles = []

    for i, title, url in articles_list:
        # bad prompt and bad data collection
        ranking = llm.predict(f"Here is an article title: {title}. Rate it on a scale of 1-10 based on this user input: {user_input}. Print only a single number.")

        # Ensure the ranking is a number. Need to change w / new prompt
        try:
            ranking = float(ranking)
        except ValueError:
            print(f"Failed to convert ranking to a number: {ranking}")
            ranking = None

        full_text = get_article_text(url)

        ranked_articles.append({
            'number': i,
            'title': title,
            'url': url,
            'rank': ranking,
            'text': full_text,
        })

    return ranked_articles

def display_articles(articles, number_of_articles):
    st.subheader(f"Top {number_of_articles} Articles:")
    for article in articles[:number_of_articles]:
        st.markdown(f"### [{article['title']}]({article['url']})")
        st.write(article['text'])
        st.markdown(f"[Read more]({article['url']})")
        st.write("---")

st.title('MyRithm')
st.write('Welcome to the MyRithm! We use AI to help you take control of your online experience. Please enter your preferences and select the number of articles you would like to see.')

# Create an input field for user preferences
user_input = st.text_input("Enter your preferences for articles:")
number_of_articles = st.slider("Select the number of articles you'd like to see:", min_value=1, max_value=10)

if user_input and number_of_articles:
    llm = ChatOpenAI(model_name='gpt-3.5-turbo', openai_api_key=api_key)
    articles_list = get_articles_list()
    ranked_articles = rank_articles(articles_list=articles_list, llm=llm, user_input=user_input)
    sorted_articles = sorted(ranked_articles, key=lambda x: x['rank'], reverse=True)
    top_articles = sorted_articles[:number_of_articles]
    display_articles(top_articles, number_of_articles)