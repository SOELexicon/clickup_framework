"""
Project Templates Module for ClickUp JSON Manager

This module defines predefined project templates that can be used with the init command.
Each template provides a structure of spaces, folders, and lists optimized for different
project types.

Task: tsk_project_templates - Project Template Definitions
"""

from typing import Dict, List, Any, Optional


# Agile Project Template
AGILE_TEMPLATE = {
    "name": "Agile Software Development",
    "spaces": [
        {
            "name": "Product Development",
            "folders": [
                {
                    "name": "Current Sprint",
                    "lists": [
                        {"name": "Backlog"},
                        {"name": "In Progress"},
                        {"name": "Code Review"},
                        {"name": "Testing"},
                        {"name": "Done"},
                    ]
                },
                {
                    "name": "Backlog",
                    "lists": [
                        {"name": "Features"},
                        {"name": "Bugs"},
                        {"name": "Technical Debt"},
                        {"name": "Improvements"},
                    ]
                },
                {
                    "name": "Releases",
                    "lists": [
                        {"name": "Next Release"},
                        {"name": "Future Releases"},
                        {"name": "Release Planning"},
                    ]
                }
            ]
        },
        {
            "name": "Product Management",
            "folders": [
                {
                    "name": "Planning",
                    "lists": [
                        {"name": "Roadmap"},
                        {"name": "Feature Requests"},
                        {"name": "User Research"},
                        {"name": "Competitive Analysis"},
                    ]
                },
                {
                    "name": "Documentation",
                    "lists": [
                        {"name": "User Guides"},
                        {"name": "API Documentation"},
                        {"name": "Developer Docs"},
                    ]
                }
            ]
        }
    ]
}


# Software Project Template
SOFTWARE_TEMPLATE = {
    "name": "Software Project",
    "spaces": [
        {
            "name": "Development",
            "folders": [
                {
                    "name": "Frontend",
                    "lists": [
                        {"name": "UI Components"},
                        {"name": "Pages"},
                        {"name": "User Flows"},
                        {"name": "UX Improvements"},
                    ]
                },
                {
                    "name": "Backend",
                    "lists": [
                        {"name": "API Endpoints"},
                        {"name": "Database"},
                        {"name": "Authentication"},
                        {"name": "Services"},
                    ]
                },
                {
                    "name": "Infrastructure",
                    "lists": [
                        {"name": "DevOps"},
                        {"name": "Deployment"},
                        {"name": "Monitoring"},
                        {"name": "Security"},
                    ]
                }
            ]
        },
        {
            "name": "Product",
            "folders": [
                {
                    "name": "Requirements",
                    "lists": [
                        {"name": "User Stories"},
                        {"name": "Epics"},
                        {"name": "Specifications"},
                    ]
                },
                {
                    "name": "Testing",
                    "lists": [
                        {"name": "Unit Tests"},
                        {"name": "Integration Tests"},
                        {"name": "E2E Tests"},
                        {"name": "QA Tasks"},
                    ]
                }
            ]
        },
        {
            "name": "Business",
            "folders": [
                {
                    "name": "Marketing",
                    "lists": [
                        {"name": "Website"},
                        {"name": "Social Media"},
                        {"name": "Content"},
                    ]
                },
                {
                    "name": "Support",
                    "lists": [
                        {"name": "Customer Issues"},
                        {"name": "Knowledge Base"},
                        {"name": "Feature Requests"},
                    ]
                }
            ]
        }
    ]
}


# Marketing Project Template
MARKETING_TEMPLATE = {
    "name": "Marketing Campaign",
    "spaces": [
        {
            "name": "Campaign Planning",
            "folders": [
                {
                    "name": "Strategy",
                    "lists": [
                        {"name": "Goals & KPIs"},
                        {"name": "Target Audience"},
                        {"name": "Messaging"},
                        {"name": "Budget"},
                    ]
                },
                {
                    "name": "Content",
                    "lists": [
                        {"name": "Blog Posts"},
                        {"name": "Social Media"},
                        {"name": "Email Campaigns"},
                        {"name": "Videos"},
                        {"name": "Graphics"},
                    ]
                }
            ]
        },
        {
            "name": "Campaign Execution",
            "folders": [
                {
                    "name": "Channels",
                    "lists": [
                        {"name": "Website"},
                        {"name": "Social Media"},
                        {"name": "Email"},
                        {"name": "Ads"},
                        {"name": "Events"},
                    ]
                },
                {
                    "name": "Timeline",
                    "lists": [
                        {"name": "Pre-launch"},
                        {"name": "Launch Day"},
                        {"name": "First Week"},
                        {"name": "Ongoing"},
                    ]
                }
            ]
        },
        {
            "name": "Analytics & Results",
            "folders": [
                {
                    "name": "Performance",
                    "lists": [
                        {"name": "Traffic"},
                        {"name": "Conversions"},
                        {"name": "Engagement"},
                        {"name": "ROI Analysis"},
                    ]
                },
                {
                    "name": "Reporting",
                    "lists": [
                        {"name": "Weekly Reports"},
                        {"name": "Post-campaign Analysis"},
                        {"name": "Insights & Learnings"},
                    ]
                }
            ]
        }
    ]
}


# Research Project Template
RESEARCH_TEMPLATE = {
    "name": "Research Project",
    "spaces": [
        {
            "name": "Project Planning",
            "folders": [
                {
                    "name": "Objectives",
                    "lists": [
                        {"name": "Research Questions"},
                        {"name": "Hypotheses"},
                        {"name": "Scope & Limitations"},
                    ]
                },
                {
                    "name": "Resources",
                    "lists": [
                        {"name": "Team"},
                        {"name": "Budget"},
                        {"name": "Timeline"},
                        {"name": "Equipment"},
                    ]
                },
                {
                    "name": "Methodology",
                    "lists": [
                        {"name": "Research Design"},
                        {"name": "Data Collection Methods"},
                        {"name": "Analysis Techniques"},
                        {"name": "Ethics & Compliance"},
                    ]
                }
            ]
        },
        {
            "name": "Data Collection",
            "folders": [
                {
                    "name": "Primary Research",
                    "lists": [
                        {"name": "Interviews"},
                        {"name": "Surveys"},
                        {"name": "Observations"},
                        {"name": "Experiments"},
                    ]
                },
                {
                    "name": "Secondary Research",
                    "lists": [
                        {"name": "Literature Review"},
                        {"name": "Data Sets"},
                        {"name": "Case Studies"},
                    ]
                }
            ]
        },
        {
            "name": "Analysis & Publication",
            "folders": [
                {
                    "name": "Data Analysis",
                    "lists": [
                        {"name": "Qualitative Analysis"},
                        {"name": "Quantitative Analysis"},
                        {"name": "Interpretation"},
                        {"name": "Visualizations"},
                    ]
                },
                {
                    "name": "Publication",
                    "lists": [
                        {"name": "Drafts"},
                        {"name": "Peer Review"},
                        {"name": "Final Publication"},
                        {"name": "Presentation Materials"},
                    ]
                }
            ]
        }
    ]
}


# Simple Project Template
SIMPLE_TEMPLATE = {
    "name": "Simple Project",
    "spaces": [
        {
            "name": "Project Management",
            "folders": [
                {
                    "name": "Tasks",
                    "lists": [
                        {"name": "To Do"},
                        {"name": "In Progress"},
                        {"name": "Done"},
                    ]
                },
                {
                    "name": "Planning",
                    "lists": [
                        {"name": "Ideas"},
                        {"name": "Resources"},
                        {"name": "Timeline"},
                    ]
                }
            ]
        }
    ]
}


# Dictionary of all available templates
TEMPLATES = {
    "agile": AGILE_TEMPLATE,
    "software": SOFTWARE_TEMPLATE,
    "marketing": MARKETING_TEMPLATE,
    "research": RESEARCH_TEMPLATE,
    "simple": SIMPLE_TEMPLATE,
}


def get_template_names() -> List[str]:
    """Get a list of available template names.
    
    Returns:
        List of template names
    """
    return list(TEMPLATES.keys())


def get_template(template_name: str) -> Dict[str, Any]:
    """Get a template by name.
    
    Args:
        template_name: Name of the template to get
        
    Returns:
        Template structure or None if not found
        
    Raises:
        ValueError: If the template name is not found
    """
    if template_name not in TEMPLATES:
        raise ValueError(f"Template '{template_name}' not found. Available templates: {', '.join(get_template_names())}")
    
    return TEMPLATES[template_name] 