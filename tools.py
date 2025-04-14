# tools.py
# Contains custom tool functions for ADK:
# - vertex_ai_search: Vertex AI Search
# - google_search: Google 検索 API

# --- Prerequisites ---
# 1. Install necessary Google Cloud & HTTP client libraries:
#    pip install google-cloud-discoveryengine requests
# 2. Authentication:
#    - For Vertex AI: Ensure ADC is set up (gcloud auth application-default login)
#      or service account has permissions ('roles/discoveryengine.viewer').
#    - For Google Custom Search: Obtain an API Key and Search Engine ID (CX).
# 3. Environment Variables: Set the following environment variables:
#    - GOOGLE_CLOUD_PROJECT: Your GCP project ID.
#    - GOOGLE_API_KEY: Your Google Custom Search API Key.
#    - GOOGLE_CSE_ID: Your Google Custom Search Engine ID (CX).
# ---------------------
import sys
from google_search_agent.agent import google_search
from vertex_ai_search_agent.agent import vertex_ai_search


if __name__ == "__main__":
    args = sys.argv
    test_query_vertex = args[1]
    test_query_google = args[2]

    # --- Vertex AI Search のテスト ---
    print(f"\n--- Vertex AI Search 検索クエリ: '{test_query_vertex}' ---")
    vertex_result = vertex_ai_search(test_query_vertex)

    if "error" in vertex_result:
        print(f"検索失敗: {vertex_result['error']}")

    elif vertex_result.get("results"):
        print("--- Vertex AI Search 結果 ---")
        for i, res in enumerate(vertex_result["results"]):
            print(f"{i+1}. URL: {res.get('url')}")
            # print(f"   Answer: {res.get('answer')}")
            # print(f"   Segment: {res.get('segment')}")
            print(f"   Snippet: {res.get('snippet')}")
            print("-" * 10)
    else:
        print("Vertex AI Search 検索結果がありません.")

    # --- Google 検索 API のテスト ---
    print(f"\n--- Google 検索クエリ: '{test_query_google}' ---")
    google_result = google_search(test_query_google)

    if "error" in google_result:
        print(f"検索失敗: {vertex_result['error']}")

    elif google_result.get("results"):
        print("--- Google 検索結果 ---")
        for i, res in enumerate(google_result["results"]):
            print(f"{i+1}. Title: {res.get('title')}")
            print(f"   URL: {res.get('url')}")
            print(f"   Snippet: {res.get('snippet')}")
            print("-" * 10)
    else:
        print("Google 検索結果がありません.")
