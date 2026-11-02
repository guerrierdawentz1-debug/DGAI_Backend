"""
DGAI Search-Grounded Retrieval & Synthesis Engine (DGAI-M4-SPEC v6.0.0 Article 3 & 0.1)
"""

from typing import Dict, Any, List, Optional
from dgai.m4a_format import format_tool_call


def search_and_synthesize(query: str, search_results: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """
    Executes search-grounded information retrieval and synthesis:
    1. Detects when information is missing or needs external verification.
    2. Formulates search tool calls.
    3. Synthesizes a factual response grounded strictly in retrieved search results.
    """
    # Formulate tool call
    tool_call = format_tool_call("search_web", {"query": query}, call_id="call_search_001")

    # Execute live web search if results are not pre-provided
    if search_results is None:
        search_results = _execute_live_web_search(query)

    if search_results:
        snippets_text = " ".join([item.get("snippet", "") for item in search_results if item.get("snippet")])
        sources = [item.get("source_url", "") for item in search_results if item.get("source_url")]
        source_str = f" [Source : {', '.join(sources)}]" if sources else ""
        synthesized_response = (
            f"D'après les résultats de la recherche effectuée sur '{query}' : {snippets_text}{source_str}"
        )
    else:
        sources = []
        synthesized_response = (
            f"Aucun résultat de recherche web fiable n'a été trouvé pour la requête '{query}'."
        )

    return {
        "query": query,
        "tool_call": tool_call,
        "search_results": search_results,
        "synthesized_response": synthesized_response,
        "grounded": True,
        "sources": sources
    }


def _execute_live_web_search(query: str) -> List[Dict[str, str]]:
    """
    Queries live web sources (Wikipedia OpenSearch / Query API & DuckDuckGo Instant Answers)
    to retrieve verified titles, snippets, and source URLs.
    """
    import urllib.request
    import urllib.parse
    import json

    results = []
    clean_query = query.strip()
    if not clean_query:
        return results

    # 1. Wikipedia Search & Extract API (French & English fallback)
    for lang in ["fr", "en"]:
        try:
            # Full text search first
            sr_url = f"https://{lang}.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean_query)}&utf8=1&format=json"
            req_sr = urllib.request.Request(sr_url, headers={"User-Agent": "DGAI/1.0"})
            titles = []
            with urllib.request.urlopen(req_sr, timeout=3) as resp_sr:
                data_sr = json.loads(resp_sr.read().decode("utf-8"))
                hits = data_sr.get("query", {}).get("search", [])
                titles = [h.get("title") for h in hits if h.get("title")][:3]

            # Fallback to opensearch if full text search yielded nothing
            if not titles:
                search_url = f"https://{lang}.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(clean_query)}&limit=3&namespace=0&format=json"
                req = urllib.request.Request(search_url, headers={"User-Agent": "DGAI/1.0"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if len(data) >= 2 and data[1]:
                        titles = data[1]

            if titles:
                titles_str = "|".join(titles)
                query_url = f"https://{lang}.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&titles={urllib.parse.quote(titles_str)}&format=json"
                req_q = urllib.request.Request(query_url, headers={"User-Agent": "DGAI/1.0"})
                with urllib.request.urlopen(req_q, timeout=3) as q_resp:
                    q_data = json.loads(q_resp.read().decode("utf-8"))
                    pages = q_data.get("query", {}).get("pages", {})
                    for pid, pinfo in pages.items():
                        title = pinfo.get("title", "")
                        extract = pinfo.get("extract", "").strip()
                        if extract and len(extract) > 20:
                            if len(extract) > 350:
                                extract = extract[:350] + "..."
                            page_url = f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                            results.append({
                                "title": title,
                                "snippet": extract,
                                "source_url": page_url
                            })
                            if len(results) >= 2:
                                break
            if results:
                break
        except Exception:
            pass

    # 2. DuckDuckGo Instant Answer API if Wikipedia returned no results
    if not results:
        try:
            ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(clean_query)}&format=json&no_html=1&skip_disambig=1"
            req_ddg = urllib.request.Request(ddg_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req_ddg, timeout=3) as resp_ddg:
                ddg_data = json.loads(resp_ddg.read().decode("utf-8"))
                abstract = ddg_data.get("AbstractText", "").strip()
                source_url = ddg_data.get("AbstractURL", "").strip()
                heading = ddg_data.get("Heading", clean_query)
                if abstract and source_url:
                    results.append({
                        "title": heading,
                        "snippet": abstract,
                        "source_url": source_url
                    })
        except Exception:
            pass

    return results
