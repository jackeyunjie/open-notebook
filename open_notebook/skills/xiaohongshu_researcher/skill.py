"""Xiaohongshu Researcher Skill.

Automatically searches and analyzes content about "solopreneur" topics
on Xiaohongshu (Little Red Book), extracts viral note patterns, and
saves findings to Notebook for further analysis.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from playwright.async_api import Browser, Page, async_playwright

from open_notebook.database.repository import repo_create, repo_query


class XiaohongshuResearcherSkill:
    """Skill for researching solopreneur topics on Xiaohongshu."""

    def __init__(self):
        self.base_url = "https://www.xiaohongshu.com"
        self.search_url = "https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search_result_notes"
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def initialize(self) -> None:
        """Initialize browser and page."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Show browser for debugging
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        
        self.page = await self.browser.new_page(
            viewport={"width": 1920, "height": 1080}
        )
        
        # Set user agent to avoid detection
        await self.page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    async def close(self) -> None:
        """Close browser."""
        if self.browser:
            await self.browser.close()

    async def search_keyword(self, keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for a keyword and collect note data.
        
        Args:
            keyword: Search keyword
            max_results: Maximum notes to collect
            
        Returns:
            List of note data dictionaries
        """
        logger.info(f"Searching for: {keyword}")
        
        notes = []
        url = self.search_url.format(keyword=keyword)
        
        try:
            await self.page.goto(url, wait_until="networkidle")
            await asyncio.sleep(3)  # Wait for content to load
            
            # Scroll to load more results
            for _ in range(3):
                await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(2)
            
            # Extract note cards with multiple selector strategies
            selectors_to_try = [
                ".note-item",                    # Original selector
                "[data-type='note']",            # Data attribute selector
                ".search-result-item",           # Search result item
                "article[role='article']",       # Semantic article tag
                ".note-card",                    # Card-style selector
                "div[class*='note']",            # Partial class match
            ]
            
            note_cards = []
            for selector in selectors_to_try:
                try:
                    note_cards = await self.page.query_selector_all(selector)
                    if note_cards:
                        logger.info(f"Found {len(note_cards)} note cards using selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Selector '{selector}' failed: {e}")
                    continue
            
            if not note_cards:
                # Fallback: try to find any clickable content items
                logger.warning("No standard selectors matched, trying generic content containers...")
                note_cards = await self.page.query_selector_all("div[class*='content'], div[class*='item']")
                logger.info(f"Found {len(note_cards)} potential content items with generic selectors")
            
            logger.info(f"Found {len(note_cards)} note cards")
            
            for i, card in enumerate(note_cards[:max_results]):
                try:
                    note_data = await self.extract_note_data(card)
                    if note_data:
                        notes.append(note_data)
                        logger.debug(f"Extracted note {i+1}: {note_data.get('title', 'N/A')[:50]}")
                except Exception as e:
                    logger.warning(f"Failed to extract note {i+1}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Search failed for {keyword}: {e}")
        
        return notes

    async def extract_note_data(self, card_element) -> Optional[Dict[str, Any]]:
        """Extract data from a single note card.
        
        Args:
            card_element: Playwright element handle for note card
            
        Returns:
            Dictionary with note data or None if extraction fails
        """
        try:
            # Extract title with multiple strategies
            title_selectors = [".title", "h3", "[class*='title']", "[data-type='title']"]
            title = ""
            for selector in title_selectors:
                title_elem = await card_element.query_selector(selector)
                if title_elem:
                    title = await title_elem.inner_text()
                    if title:
                        break
            
            # Extract author with multiple strategies
            author_selectors = [".nickname", "[class*='author']", "[class*='user']", "[data-type='author']"]
            author = ""
            for selector in author_selectors:
                author_elem = await card_element.query_selector(selector)
                if author_elem:
                    author = await author_elem.inner_text()
                    if author:
                        break
            
            # Extract engagement metrics - use flexible selectors
            like_count = "0"
            collect_count = "0"
            
            # Strategy 1: Look for icons with text content
            icon_containers = await card_element.query_selector_all("[class*='icon'], [class*='interaction'], [class*='engage']")
            for container in icon_containers:
                container_text = await container.inner_text()
                if container_text:
                    # Try to extract numbers from the text
                    import re
                    numbers = re.findall(r'\d+', container_text)
                    if numbers:
                        if '👍' in container_text or 'like' in container_text.lower():
                            like_count = numbers[0]
                        elif '⭐' in container_text or 'collect' in container_text.lower() or 'star' in container_text.lower():
                            collect_count = numbers[0]
            
            # Strategy 2: Fallback - look for any number-like text near icons
            if like_count == "0" or collect_count == "0":
                all_numbers = await card_element.query_selector_all("span, div")
                for elem in all_numbers:
                    text = await elem.inner_text()
                    if text and any(c.isdigit() for c in text):
                        import re
                        numbers = re.findall(r'\d+', text)
                        if numbers:
                            parent_class = await elem.evaluate("el => el.parentElement.className")
                            if 'like' in parent_class.lower() or '👍' in text:
                                like_count = numbers[0]
                            elif 'collect' in parent_class.lower() or 'star' in parent_class.lower() or '⭐' in text:
                                collect_count = numbers[0]
            
            # Extract link with multiple strategies
            link_selectors = ["a.cover", "a[href*='/explore/']", "a[href*='/discovery/']", "[role='link']"]
            link = ""
            for selector in link_selectors:
                link_elem = await card_element.query_selector(selector)
                if link_elem:
                    link = await link_elem.get_attribute("href")
                    if link:
                        break
            
            # If still no link, try to get it from the card itself
            if not link:
                link = await card_element.evaluate("""el => {
                    const anchor = el.closest('a');
                    return anchor ? anchor.href : '';
                }""")
            
            # Clean up counts (remove commas, convert to int)
            like_count = int(like_count.replace(",", "").replace("万", "0000")) if like_count else 0
            collect_count = int(collect_count.replace(",", "").replace("万", "0000")) if collect_count else 0
            
            return {
                "title": title.strip(),
                "author": author.strip(),
                "like_count": like_count,
                "collect_count": collect_count,
                "url": self.base_url + link if link.startswith("/") else link,
                "search_keyword": await card_element.evaluate("el => el.closest('[data-type=search]').dataset.keyword"),
                "collected_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Error extracting note data: {e}")
            return None

    async def analyze_patterns(self, notes: List[Dict[str, Any]]) -> List[str]:
        """Analyze collected notes to identify viral patterns.
        
        Args:
            notes: List of note data dictionaries
            
        Returns:
            List of insight strings
        """
        insights = []
        
        if not notes:
            return insights
        
        # Analyze title patterns
        titles = [n["title"] for n in notes if n.get("like_count", 0) > 100]
        if titles:
            # Check for numbers in titles
            num_with_digits = sum(1 for t in titles if any(c.isdigit() for c in t))
            if num_with_digits / len(titles) > 0.6:
                insights.append("爆款标题多包含数字（60% 以上高赞笔记使用）")
            
            # Check for emotional words
            emotional_words = ["太", "超", "真的", "绝了", "必看", "干货"]
            num_emotional = sum(1 for t in titles if any(w in t for w in emotional_words))
            if num_emotional / len(titles) > 0.5:
                insights.append("情绪词使用频繁（50% 以上标题包含强烈情感表达）")
        
        # Analyze engagement distribution
        avg_likes = sum(n.get("like_count", 0) for n in notes) / len(notes)
        avg_collects = sum(n.get("collect_count", 0) for n in notes) / len(notes)
        
        insights.append(f"平均点赞数：{avg_likes:.0f}")
        insights.append(f"平均收藏数：{avg_collects:.0f}")
        
        # Collect-to-like ratio
        if avg_likes > 0:
            ratio = avg_collects / avg_likes
            if ratio > 0.3:
                insights.append(f"收藏/点赞比={ratio:.2f}，内容实用性强（用户倾向于收藏）")
        
        # Top authors
        author_counts = {}
        for note in notes:
            author = note.get("author", "Unknown")
            author_counts[author] = author_counts.get(author, 0) + 1
        
        top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_authors:
            insights.append(f"活跃创作者：{', '.join([a[0] for a in top_authors])}")
        
        return insights

    async def save_to_notebook(self, keyword: str, notes: List[Dict[str, Any]], insights: List[str]) -> int:
        """Save research results to Notebook.
        
        Args:
            keyword: Search keyword
            notes: List of note data
            insights: Analysis insights
            
        Returns:
            Number of sources created
        """
        today = datetime.now().strftime("%Y-%m-%d")
        notebook_name = f"小红书研究 - {today}"
        
        # Find or create notebook
        existing = await repo_query(
            f"SELECT * FROM notebook WHERE name = '{notebook_name}'"
        )
        
        if existing:
            notebook_id = existing[0]["id"]
        else:
            notebook_data = {
                "name": notebook_name,
                "description": f"自动收集的小红书'{keyword}'相关内容研究数据",
                "created_at": datetime.now()
            }
            result = await repo_create("notebook", notebook_data)
            notebook_id = result["id"]
        
        # Create source with all notes
        source_data = {
            "notebook_id": notebook_id,
            "title": f"{keyword} - 爆款笔记分析 ({len(notes)}篇)",
            "source_type": "xiaohongshu_research",
            "url": f"https://www.xiaohongshu.com/search_result?keyword={keyword}",
            "content": json.dumps({
                "notes": notes,
                "insights": insights,
                "summary": {
                    "total_notes": len(notes),
                    "keyword": keyword,
                    "collected_at": datetime.now().isoformat()
                }
            }, ensure_ascii=False, indent=2),
            "metadata": {
                "research_type": "xiaohongshu",
                "keyword": keyword,
                "note_count": len(notes),
                "insight_count": len(insights)
            }
        }
        
        result = await repo_create("source", source_data)
        logger.info(f"Saved research to source: {result['id']}")
        
        return 1

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the research skill.
        
        Args:
            params: Execution parameters
                - keywords: List of keywords to search
                - max_results: Max results per keyword (default: 10)
                - save_to_notebook: Whether to save to notebook (default: True)
                
        Returns:
            Execution results
        """
        keywords = params.get("keywords", ["一人公司"])
        max_results = params.get("max_results", 10)
        save_to_notebook = params.get("save_to_notebook", True)
        
        logger.info(f"Starting Xiaohongshu research: {keywords}")
        
        await self.initialize()
        
        try:
            all_notes = []
            total_sources = 0
            
            for keyword in keywords:
                # Search and collect
                notes = await self.search_keyword(keyword, max_results)
                all_notes.extend(notes)
                
                # Analyze patterns
                insights = await self.analyze_patterns(notes)
                
                # Save to notebook
                if save_to_notebook and notes:
                    sources = await self.save_to_notebook(keyword, notes, insights)
                    total_sources += sources
                
                # Rate limiting
                if keyword != keywords[-1]:
                    await asyncio.sleep(3)
            
            return {
                "total_notes": len(all_notes),
                "sources_created": total_sources,
                "insights": await self.analyze_patterns(all_notes),
                "keywords_searched": keywords
            }
            
        finally:
            await self.close()


# Convenience function for direct usage
async def research_xiaohongshu(
    keywords: List[str] = ["一人公司"],
    max_results: int = 10,
    save_to_notebook: bool = True
) -> Dict[str, Any]:
    """Convenience function to run Xiaohongshu research.
    
    Args:
        keywords: Keywords to search
        max_results: Max results per keyword
        save_to_notebook: Whether to save to notebook
        
    Returns:
        Research results dictionary
    """
    skill = XiaohongshuResearcherSkill()
    return await skill.execute({
        "keywords": keywords,
        "max_results": max_results,
        "save_to_notebook": save_to_notebook
    })
