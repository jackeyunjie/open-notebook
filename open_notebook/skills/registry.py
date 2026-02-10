"""Skill registry for discovering and managing skills.

The registry maintains a mapping of skill types to their classes,
enabling dynamic skill instantiation from configuration.
"""

from typing import Dict, List, Optional, Type

from open_notebook.skills.base import Skill, SkillConfig


class SkillRegistry:
    """Central registry for all available skills.
    
    Usage:
        # Register a skill
        SkillRegistry.register(RssCrawlerSkill)
        
        # Create skill instance from config
        config = SkillConfig(skill_type="rss_crawler", ...)
        skill = SkillRegistry.create(config)
        
        # List available skills
        available = SkillRegistry.list_skills()
    """
    
    _skills: Dict[str, Type[Skill]] = {}
    
    @classmethod
    def register(cls, skill_class: Type[Skill]) -> Type[Skill]:
        """Register a skill class.
        
        Can be used as a decorator:
            @SkillRegistry.register
            class MySkill(Skill):
                ...
        
        Args:
            skill_class: The skill class to register
            
        Returns:
            The registered class (for decorator use)
        """
        skill_type = skill_class.skill_type
        if skill_type in cls._skills:
            raise ValueError(f"Skill type '{skill_type}' is already registered")
        
        cls._skills[skill_type] = skill_class
        return skill_class
    
    @classmethod
    def unregister(cls, skill_type: str) -> None:
        """Unregister a skill type."""
        if skill_type in cls._skills:
            del cls._skills[skill_type]
    
    @classmethod
    def create(cls, config: SkillConfig) -> Skill:
        """Create a skill instance from configuration.
        
        Args:
            config: Skill configuration with skill_type
            
        Returns:
            Instantiated skill
            
        Raises:
            ValueError: If skill_type is not registered
        """
        skill_type = config.skill_type
        skill_class = cls._skills.get(skill_type)
        
        if skill_class is None:
            raise ValueError(
                f"Unknown skill type: '{skill_type}'. "
                f"Available: {list(cls._skills.keys())}"
            )
        
        return skill_class(config)
    
    @classmethod
    def list_skills(cls) -> List[Dict[str, str]]:
        """List all registered skills with metadata.
        
        Returns:
            List of skill metadata dicts with keys:
            - skill_type
            - name
            - description
        """
        return [
            {
                "skill_type": skill_class.skill_type,
                "name": skill_class.name,
                "description": skill_class.description,
            }
            for skill_class in cls._skills.values()
        ]
    
    @classmethod
    def get_skill_class(cls, skill_type: str) -> Optional[Type[Skill]]:
        """Get skill class by type.
        
        Args:
            skill_type: The skill type identifier
            
        Returns:
            Skill class or None if not found
        """
        return cls._skills.get(skill_type)
    
    @classmethod
    def is_registered(cls, skill_type: str) -> bool:
        """Check if a skill type is registered."""
        return skill_type in cls._skills
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registrations. Useful for testing."""
        cls._skills.clear()


def register_skill(skill_class: Type[Skill]) -> Type[Skill]:
    """Convenience decorator for registering skills.
    
    Usage:
        @register_skill
        class MySkill(Skill):
            skill_type = "my_skill"
            ...
    """
    return SkillRegistry.register(skill_class)
