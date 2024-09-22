import streamlit as st
import requests
from algoliasearch.search_client import SearchClient
import logging
import pprint
import os

from dotenv import load_dotenv

load_dotenv()

ALGOLIA_APP_ID = os.getenv("ALGOLIA_APP_ID")
ALGOLIA_WRITE_API_KEY = os.getenv("ALGOLIA_WRITE_API_KEY")
ALGOLIA_API_KEY = os.getenv("ALGOLIA_API_KEY")
ALGOLIA_INDEX_NAME = os.getenv("ALGOLIA_INDEX_NAME")
GPT_KEY = os.getenv("GPT_KEY")
client = SearchClient.create(ALGOLIA_APP_ID, ALGOLIA_API_KEY)
index = client.init_index(ALGOLIA_INDEX_NAME)


def index_ticket(ticket_id, ticket_content, ticket_answer):
    index.save_object({
        'objectID': ticket_id,
        'ticket_content': ticket_content,
        'ticket_answer': ticket_answer
    })


def write_to_index(ticket_id, ticket_content, ticket_answer):
    client = SearchClient.create(ALGOLIA_APP_ID, ALGOLIA_WRITE_API_KEY)
    index = client.init_index(ALGOLIA_INDEX_NAME)

    try:
        ticket = {
            'objectID': ticket_id,
            'ticket_content': ticket_content,
            'ticket_answer': ticket_answer
        }

        index.save_object(ticket)
        print(f"Ticket '{ticket_id}' has been successfully indexed.")

    except Exception as e:
        logging.error(f"Failed to index ticket '{ticket_id}': {e}")


def get_similar_tickets(new_ticket_content):
    results = index.search(new_ticket_content, {'hitsPerPage': 5})
    return results['hits']


def get_all_tickets():
    all_tickets = []
    for ticket in index.browse_objects():
        all_tickets.append(ticket)
    return all_tickets


def send_request(prompt):
    url = "https://infinite-gpt.p.rapidapi.com/infinite-gpt"

    payload = {
        "query": prompt,
        "sysMsg": "You are a happy helpful assistant"
    }
    headers = {
        "x-rapidapi-key": GPT_KEY,
        "x-rapidapi-host": "infinite-gpt.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    print(response.json())
    result = response.json()
    pprint.pprint(result)
    if "msg" in result:
        return result["msg"]
    else:
        return "Error generating response or unexpected response format."


def generate_response(new_ticket, similar_tickets=None):
    prompt = f"Ticket: {new_ticket}\n\n"

    if similar_tickets:
        prompt += "Similar Tickets and Answers:\n"
        for i, ticket in enumerate(similar_tickets, 1):
            prompt += f"{i}. {ticket['ticket_content']} - Answer: {ticket['ticket_answer']}\n"
    else:
        prompt += "No similar tickets found. Please provide an answer to the ticket."

    print(prompt)
    return send_request(prompt=prompt)




st.title('Support Ticket System')

new_ticket = st.text_area("Enter your ticket details:")

if st.button('Submit Ticket'):
    if new_ticket:
        similar_tickets = get_similar_tickets(new_ticket)

        if similar_tickets:
            st.subheader("Similar Tickets Found:")
            for ticket in similar_tickets:
                st.write(f"Ticket: {ticket['ticket_content']}")
                st.write(f"Answer: {ticket['ticket_answer']}")
                st.write("---")
            enhanced_response = generate_response(new_ticket, similar_tickets if similar_tickets else None)

        if not similar_tickets:
            all_tickets = get_all_tickets()
            enhanced_response = generate_response(new_ticket, all_tickets)
            new_ticket_id = str(int(index.search('').get('nbHits', 0)) + 1)
            write_to_index(new_ticket_id, new_ticket, enhanced_response)

        st.subheader("Enhanced Response:")
        st.write(enhanced_response)
    else:
        st.write("Please enter ticket details.")
