# helper.py (Updated for API Integration and Scoring Queries)
import os
import subprocess
import requests
import aiohttp
from datetime import datetime
from typing import Dict, List, Any
from bs4 import BeautifulSoup
from gtts import gTTS
import asyncio
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from logger.app_logger import app_logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ========== OLLAMA SAFE RUNNER ========== #
def run_llama_prompt(prompt: str, timeout: int = 60, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            result = subprocess.run(
                ["ollama", "run", "llama3.2:latest"],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8"
            )
            if result.returncode == 0:
                app_logger.log_info("Ollama generated response successfully.")
                return result.stdout.strip()
            else:
                app_logger.log_error(f"Ollama model error: {result.stderr.strip()}")
                return f"⚠️ Model error: {result.stderr.strip()}"
        except subprocess.TimeoutExpired:
            app_logger.log_warning("Ollama model timeout occurred.")
            if attempt < retries - 1:
                continue
            return "⚠️ Timeout from model after retries."
        except Exception as e:
            app_logger.log_error(f"Exception in run_llama_prompt: {e}")
            return f"⚠️ Exception: {e}"
    return "⚠️ Model failed."

# ========== CHATBOT ========== #
class ChatBot:
    def __init__(self):
        self.history: List[Dict[str, str]] = [{"role": "system", "content": "You are a helpful assistant."}]

    def generate_response(self, prompt: str) -> str:
        self.history.append({"role": "user", "content": prompt})
        chat_log = "\n".join(f"{m['role']}: {m['content']}" for m in self.history)
        return run_llama_prompt(chat_log)

    @staticmethod
    def rate_article_sync(title: str, content: str) -> str:
        prompt = f"""
Rate this article from 1–5 based on relevance and quality.\nTitle: {title}\nContent: {content[:1000]}\nOnly return a number.
"""
        return run_llama_prompt(prompt, timeout=12)

    @staticmethod
    def rate_query_sync(prompt: str) -> str:
        judge_prompt = f"""
Please rate the quality of this user query for data science use.\nGive a number 1-5 based on clarity, specificity, and usefulness:\n\nQuery: {prompt}\n\nOnly return a number.
"""
        return run_llama_prompt(judge_prompt, timeout=10)

# ========== AUDIO ========== #
def save_to_audio(text: str) -> None:
    try:
        gTTS(text=text, lang="en").save("output.mp3")
        app_logger.log_info("Saved text to audio successfully.")
    except Exception as e:
        app_logger.log_error(f"Error saving audio: {e}")

# ========== NEWS SEARCH ========== #
async def invoke_free_news_search(query: str, num: int = 5, location: str = "us-en", time_filter: str = "d") -> Dict[str, Any]:
    try:
        app_logger.log_info(f"Starting DuckDuckGo news search for query: {query}", level="INFO")

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)

        search_url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}&kl={location}&df={time_filter}&ia=news"
        driver.get(search_url)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        search_results = soup.find_all("div", class_="result__body")
        results = []

        for idx, result in enumerate(search_results[:num]):
            a_tag = result.find("a", class_="result__a") or result.find("a")
            if not a_tag:
                continue
            title = a_tag.text.strip()
            if title == "":
                continue
            href = a_tag.get("href", "")

            match = re.search(r"uddg=(https?%3A%2F%2F[^&]+)", href)
            link = urllib.parse.unquote(match.group(1)) if match else href

            snippet_tag = result.find("a", class_="result__snippet") or result.find("div", class_="result__snippet")
            summary = snippet_tag.text.strip() if snippet_tag else "No summary available."

            rating = ChatBot.rate_article_sync(title, summary)
            rating_clean = rating if rating.replace('.', '', 1).isdigit() else "N/A"

            results.append({
                "num": idx + 1,
                "title": title,
                "link": link,
                "summary": summary,
                "body": summary,
                "rating": rating_clean
            })

        app_logger.log_info(f"DuckDuckGo scraping returned {len(results)} results.")
        return {"status": "success", "results": results} if results else {"status": "error", "results": []}

    except Exception as e:
        app_logger.log_error(f"Error during DuckDuckGo scraping: {e}")
        return {"status": "error", "results": []}

# ========== STAR RATING CONVERSION ========== #
def rating_to_stars(rating: str) -> str:
    try:
        rating_val = float(rating)
        full_stars = int(rating_val)
        half_star = "⭐½" if rating_val - full_stars >= 0.5 else ""
        return "⭐" * full_stars + half_star
    except (ValueError, TypeError):
        return "N/A"

# ========== YEAR UTILITY ========== #
def current_year() -> int:
    return datetime.now().year
