"""Content crawler skill for automated source ingestion.

This skill fetches content from RSS feeds and web pages,
creating Source records in Open Notebook.
"""

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from loguru import logger

from open_notebook.domain.notebook import Source
from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


class RssCrawlerSkill(Skill):
    """Crawl RSS feeds and create sources.
    
    This skill fetches RSS feeds, extracts entries, and creates
    Source records linked to a target notebook.
    
    Parameters:
        - feed_urls: List of RSS feed URLs to crawl
        - max_entries: Maximum entries to fetch per feed (default: 10)
        - deduplicate: Whether to skip existing sources (default: true)
    
    Example:
        config = SkillConfig(
            skill_type="rss_crawler",
            name="Tech News Crawler",
            description="Fetch tech news from HackerNews",
            parameters={
                "feed_urls": ["https://news.ycombinator.com/rss"],
                "max_entries": 20,
                "deduplicate": True
            },
            target_notebook_id="notebook:abc123"
        )
    """
    
    skill_type = "rss_crawler"
    name = "RSS Content Crawler"
    description = "Automatically fetch content from RSS feeds and create sources"
    
    parameters_schema = {
        "feed_urls": {
            "type": "array",
            "items": {"type": "string", "format": "uri"},
            "description": "List of RSS feed URLs to crawl"
        },
        "max_entries": {
            "type": "integer",
            "default": 10,
            "minimum": 1,
            "maximum": 100,
            "description": "Maximum entries to fetch per feed"
        },
        "deduplicate": {
            "type": "boolean",
            "default": True,
            "description": "Skip sources that already exist (by URL hash)"
        }
    }
    
    def __init__(self, config: SkillConfig):
        super().__init__(config)
        self.feed_urls: List[str] = self.get_param("feed_urls", [])
        self.max_entries: int = self.get_param("max_entries", 10)
        self.deduplicate: bool = self.get_param("deduplicate", True)
    
    def _validate_config(self) -> None:
        """Validate RSS crawler configuration."""
        super()._validate_config()
        
        if not self.feed_urls:
            raise ValueError("At least one feed URL is required")
        
        for url in self.feed_urls:
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid URL: {url}")
    
    def _generate_source_id(self, url: str) -> str:
        """Generate a deterministic source ID from URL."""
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        return f"source:rss_{url_hash}"
    
    async def _check_source_exists(self, source_id: str) -> bool:
        """Check if a source with this ID already exists."""
        try:
            existing = await Source.get(source_id)
            return existing is not None
        except Exception:
            return False
    
    async def _parse_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """Parse RSS feed and return entries.
        
        Uses a simple approach with httpx + feedparser-style parsing.
        For production, consider using feedparser library.
        """
        logger.info(f"Fetching RSS feed: {feed_url}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(feed_url)
                response.raise_for_status()
                content = response.text
                
                # Simple RSS parsing - extract items
                # In production, use feedparser or xml.etree
                entries = self._extract_entries(content, feed_url)
                
                logger.info(f"Found {len(entries)} entries in {feed_url}")
                return entries[:self.max_entries]
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {feed_url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing {feed_url}: {e}")
            raise
    
    def _extract_entries(self, content: str, feed_url: str) -> List[Dict[str, Any]]:
        """Extract entries from RSS/XML content.
        
        This is a simplified implementation.
        For robust parsing, integrate feedparser.
        """
        import xml.etree.ElementTree as ET
        
        entries = []
        try:
            root = ET.fromstring(content)
            
            # Handle RSS 2.0
            channel = root.find("channel")
            if channel is not None:
                for item in channel.findall("item"):
                    entry = self._parse_item(item)
                    if entry:
                        entries.append(entry)
                return entries
            
            # Handle Atom
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry_elem in root.findall("atom:entry", ns):
                entry = self._parse_atom_entry(entry_elem, ns)
                if entry:
                    entries.append(entry)
            
            return entries
            
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
            return []
    
    def _parse_item(self, item) -> Optional[Dict[str, Any]]:
        """Parse RSS item element."""
        title_elem = item.find("title")
        link_elem = item.find("link")
        desc_elem = item.find("description")
        pub_date_elem = item.find("pubDate")
        
        if not link_elem or not link_elem.text:
            return None
        
        return {
            "title": title_elem.text if title_elem is not None else "Untitled",
            "url": link_elem.text,
            "description": desc_elem.text if desc_elem is not None else "",
            "published": pub_date_elem.text if pub_date_elem is not None else None,
        }
    
    def _parse_atom_entry(self, entry, ns) -> Optional[Dict[str, Any]]:
        """Parse Atom entry element."""
        title_elem = entry.find("atom:title", ns)
        link_elem = entry.find("atom:link", ns)
        summary_elem = entry.find("atom:summary", ns)
        content_elem = entry.find("atom:content", ns)
        updated_elem = entry.find("atom:updated", ns)
        
        url = link_elem.get("href") if link_elem is not None else None
        if not url:
            return None
        
        content = ""
        if summary_elem is not None and summary_elem.text:
            content = summary_elem.text
        elif content_elem is not None and content_elem.text:
            content = content_elem.text
        
        return {
            "title": title_elem.text if title_elem is not None else "Untitled",
            "url": url,
            "description": content,
            "published": updated_elem.text if updated_elem is not None else None,
        }
    
    async def _create_source(self, entry: Dict[str, Any]) -> Optional[str]:
        """Create a Source record from feed entry.
        
        Args:
            entry: Feed entry with title, url, description, published
            
        Returns:
            Source ID if created, None if skipped
        """
        url = entry.get("url")
        if not url:
            return None
        
        source_id = self._generate_source_id(url)
        
        # Check for duplicates
        if self.deduplicate and await self._check_source_exists(source_id):
            logger.debug(f"Skipping duplicate source: {url}")
            return None
        
        # Create source
        title = entry.get("title", "Untitled")
        description = entry.get("description", "")
        
        # Build full text from description
        full_text = f"# {title}\n\n{description}"
        if entry.get("published"):
            full_text += f"\n\nPublished: {entry.get('published')}"
        full_text += f"\n\nSource: {url}"
        
        try:
            source = Source(
                id=source_id,
                title=title,
                full_text=full_text,
                asset={"url": url},
                topics=["rss", "auto-import"]
            )
            await source.save()
            
            # Link to target notebook if specified
            if self.config.target_notebook_id:
                await source.add_to_notebook(self.config.target_notebook_id)
                logger.info(f"Created source {source_id} and linked to {self.config.target_notebook_id}")
            else:
                logger.info(f"Created source {source_id}")
            
            return source_id
            
        except Exception as e:
            logger.error(f"Failed to create source for {url}: {e}")
            return None
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute RSS crawling.
        
        Args:
            context: Execution context
            
        Returns:
            SkillResult with created source IDs
        """
        logger.info(f"Starting RSS crawl for {len(self.feed_urls)} feeds")
        
        created_sources: List[str] = []
        errors: List[str] = []
        total_entries = 0
        
        for feed_url in self.feed_urls:
            try:
                entries = await self._parse_feed(feed_url)
                total_entries += len(entries)
                
                for entry in entries:
                    source_id = await self._create_source(entry)
                    if source_id:
                        created_sources.append(source_id)
                
            except Exception as e:
                error_msg = f"Failed to process {feed_url}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Determine status
        if errors and not created_sources:
            status = SkillStatus.FAILED
        elif errors:
            status = SkillStatus.SUCCESS  # Partial success
        else:
            status = SkillStatus.SUCCESS
        
        return SkillResult(
            skill_id=context.skill_id,
            status=status,
            started_at=datetime.utcnow(),
            output={
                "feeds_processed": len(self.feed_urls),
                "entries_found": total_entries,
                "sources_created": len(created_sources),
                "errors": errors
            },
            error_message="; ".join(errors) if errors else None,
            created_source_ids=created_sources
        )


# Register the skill
register_skill(RssCrawlerSkill)
