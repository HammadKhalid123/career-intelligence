from urllib.parse import quote_plus


def get_learning_resources(skill: str) -> dict:
    query = quote_plus(skill)
    documentation_search_url = f"https://www.google.com/search?q={quote_plus(skill + ' official documentation')}"
    video_search_url = f"https://www.youtube.com/results?search_query={quote_plus(skill + ' tutorial')}"
    resources = [
        {"title": "Official documentation", "resource_type": "Docs", "url": documentation_search_url},
        {"title": "Official guide and tutorials", "resource_type": "Guides", "url": f"https://www.google.com/search?q={quote_plus(skill + ' official guide tutorial')}"},
        {"title": "GitHub examples", "resource_type": "Examples", "url": f"https://github.com/search?q={query}&type=repositories"},
        {"title": "YouTube tutorials", "resource_type": "Video", "url": video_search_url},
        {"title": "Practical projects", "resource_type": "Projects", "url": f"https://www.google.com/search?q={quote_plus(skill + ' practical projects examples')}"},
        {"title": "Community questions", "resource_type": "Community", "url": f"https://stackoverflow.com/search?q={query}"},
    ]

    return {
        "skill": skill,
        "documentation_search_url": documentation_search_url,
        "video_search_url": video_search_url,
        "resources": resources,
    }