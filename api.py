# api.py (FastAPI wrapper for helper.py functions)
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional
from helper import ChatBot, invoke_free_news_search, rating_to_stars
import asyncio

app = FastAPI(title="SearchBot API", description="API wrapper for ChatBot, News Search, and Rating via Ollama")


class NewsQuery(BaseModel):
    query: str
    num: int = 5
    location: str = "us-en"
    time_filter: str = "d"


@app.get("/ping")
def ping():
    return {"message": "API is live 🚀"}


@app.post("/search-news")
async def search_news(payload: NewsQuery):
    result = await invoke_free_news_search(
        query=payload.query,
        num=payload.num,
        location=payload.location,
        time_filter=payload.time_filter
    )
    return result


@app.get("/rate-query")
def rate_query_quality(prompt: str = Query(..., description="Prompt to rate")):
    """
    Rate the quality of a user query using Ollama.
    """
    judge = ChatBot()
    prompt_text = f"""
Please rate the quality of this user query for data science use. 
Give a number 1-5 based on clarity, specificity, and usefulness:

Query: {prompt}

Only return a number.
"""
    rating = judge.generate_response(prompt_text)
    return {"prompt": prompt, "rating": rating, "stars": rating_to_stars(rating)}


@app.get("/chat-response")
def generate_chat_response(prompt: str = Query(..., description="Prompt for chatbot")):
    bot = ChatBot()
    return {"response": bot.generate_response(prompt)}
