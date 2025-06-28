import re
from typing import Dict, List, Any
from openai import OpenAI
from loguru import logger
from pydantic import BaseModel
from .quality.quality_checker import QualityChecker
from .templates.template_manager import TemplateManager
from .prompts.version_control import PromptManager
from .prompts import(
    CONTEXT_ANALYSIS_PROMPT,
    SYSTEM_CONTEXT_PROMPT,
    SYSTEM_ELEMENT_PROMPT,
    USER_ELEMENT_PROMPT,
    SYSTEM_EPIC_PROMPT,
    SELECTED_PROMPT,
)
from .coverage.enhanced_coverage import EnhancedCoverageTracker
from .cache.cache_manager import CacheManager

class DesignAnalysis(BaseModel):
    """Results of AI analysis of design elements"""
    title: str
    description: str
    user_story: str
    acceptance_criteria: List[str]
    technical_requirements: List[str]
    story_points: int
    priority: str
    type: str = "Feature"

class AIProcessor:
    """Processes design elements using AI to generate user stories"""
    
    def __init__(self, api_key: str, config: dict):
        self.client = OpenAI(api_key=api_key)
        self.config = config
        self.quality_checker = QualityChecker()
        self._application_context = None
        self.context_prompt = CONTEXT_ANALYSIS_PROMPT
        self.system_prompt = SYSTEM_ELEMENT_PROMPT
        self.coverage_tracker = EnhancedCoverageTracker()
        self.cache_manager = CacheManager()
        self.prompt_manager = PromptManager()
        self.template_manager = TemplateManager()

    def _create_elements_overview(self, elements: List[Dict]) -> str:
        """Create a comprehensive overview of all elements"""
        overview = ["Application Elements Overview:"]
        
        # Group elements by type
        elements_by_type = {}
        for element in elements:
            element_type = element.get('type', 'Unknown')
            if element_type not in elements_by_type:
                elements_by_type[element_type] = []
            elements_by_type[element_type].append(element)
        
        # Create hierarchical overview
        for element_type, type_elements in elements_by_type.items():
            overview.append(f"\n{element_type} Components:")
            for element in type_elements:
                name = element.get('name', 'Unnamed')
                desc = element.get('description', 'No description')
                props = self._format_properties(element.get('properties', {}))
                overview.append(f"- {name}")
                overview.append(f"  Description: {desc}")
                overview.append(f"  Properties:\n{props}")
        
        return "\n".join(overview)

    def analyze_application_context(self, elements: List[Dict]) -> str:
        """Analyze the application context using AI"""
        try:
            # Create a comprehensive overview of all elements
            overview = self._create_elements_overview(elements)
            
            # Create the prompt with the overview
            prompt = SYSTEM_CONTEXT_PROMPT.format(elements_overview=overview)
            
            # Log the prompt being used
            logger.info(f"Using system prompt for context analysis:\n{prompt}")
            
            # Get AI completion
            completion = self.client.chat.completions.create(
                model=self.config.get("model", "gpt-3.5-turbo"),
                temperature=self.config.get("temperature", 0.3),
                messages=[
                    {"role": "system", "content": prompt}
                ]
            )
            
            # Get the message content
            message_content = completion.choices[0].message.content
            
            # Log the raw LLM response
            logger.info(f"Raw LLM response for context analysis:\n{message_content}")
            
            # Parse and store the context
            self._application_context = self._parse_context_response(message_content)
            
            # Log the parsed context for debugging
            logger.info("Parsed application context:")
            logger.info(f"Core Purpose: {self._application_context.get('core_purpose', 'N/A')}")
            logger.info("Target Users:")
            for user in self._application_context.get('target_users', []):
                logger.info(f"- {user}")
            logger.info("Key Features:")
            for feature in self._application_context.get('key_features', []):
                logger.info(f"- {feature}")
            logger.info("User Flows:")
            for flow in self._application_context.get('user_flows', []):
                logger.info(f"- {flow}")
            logger.info("Shared Components:")
            for component in self._application_context.get('shared_components', []):
                logger.info(f"- {component}")
            logger.info("Technical Architecture:")
            for tech in self._application_context.get('technical_architecture', []):
                logger.info(f"- {tech}")
            
            return message_content
        except Exception as e:
            logger.error(f"Error analyzing application context: {e}")
            raise

    def _parse_context_response(self, response: str) -> dict:
        """Parse the context response into a structured dictionary"""
        try:
            # Initialize empty dictionary for parsed data
            parsed_data = {
                "core_purpose": "",
                "target_users": [],
                "key_features": [],
                "user_flows": [],
                "shared_components": [],
                "technical_architecture": []
            }

            # Split response into sections based on headers
            sections = response.split('\n\n')
            
            for section in sections:
                if not section.strip():
                    continue
                
                # Get the section header (everything before the first colon)
                header = section.split(':')[0].strip()
                
                # Get the content (everything after the first colon)
                content = ':'.join(section.split(':')[1:]).strip()
                
                # Handle different sections based on header
                if header.lower() == "core purpose":
                    parsed_data["core_purpose"] = content
                elif header.lower() == "target users":
                    parsed_data["target_users"] = [user.strip() for user in content.split('-') if user.strip()]
                elif header.lower() == "key features":
                    parsed_data["key_features"] = [feature.strip() for feature in content.split('-') if feature.strip()]
                elif header.lower() == "user flows":
                    parsed_data["user_flows"] = [flow.strip() for flow in content.split('-') if flow.strip()]
                elif header.lower() == "shared components":
                    parsed_data["shared_components"] = [comp.strip() for comp in content.split('-') if comp.strip()]
                elif header.lower() == "technical architecture":
                    parsed_data["technical_architecture"] = [arch.strip() for arch in content.split('-') if arch.strip()]

            return parsed_data
        except Exception as e:
            logger.error(f"Error parsing context response: {e}")
            return {"error": str(e)}



    def analyze_element(self, element: Dict) -> DesignAnalysis:
        """
        Analyze a design element and generate a user story
        
        Args:
            element: Figma design element to analyze
            
        Returns:
            Analysis results including story details
        """
        try:
            # Ensure we have application context
            if not self._application_context:
                raise ValueError("Application context not analyzed. Call analyze_application_context first.")
            
            # Create detailed prompt for the element with context
            element_prompt = self._create_element_prompt(element)
            
            # Format the system prompt with the application context
            contextualized_prompt = self.system_prompt.format(
                application_context=self._format_context(self._application_context)
            )

            # Print or log the prompts and content
            print("\n--- OpenAI SYSTEM PROMPT (Element) ---\n", contextualized_prompt)
            print("\n--- OpenAI USER PROMPT (Element) ---\n", element_prompt)
            print("\n--- Figma Element ---\n", element)
            
            # Get AI completion
            response = self.client.chat.completions.create(
                model=self.config.get("model", "gpt-3.5-turbo"),
                temperature=self.config.get("temperature", 0.7),
                messages=[
                    {"role": "system", "content": contextualized_prompt},
                    {"role": "user", "content": element_prompt}
                ]
            )
            
            print("LLM Response:\n", response.choices[0].message.content)
            
            # Parse and structure the response
            return self._parse_response(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error analyzing element: {e}")
            raise

    def _format_context(self, context: Dict) -> str:
        """Format application context for the prompt"""
        sections = [
            f"Core Purpose: {context['core_purpose']}",
            "\nTarget Users:",
            *[f"- {user}" for user in context['target_users']],
            "\nKey Features:",
            *[f"- {feature}" for feature in context['key_features']],
            "\nUser Flows:",
            *[f"- {flow}" for flow in context['user_flows']],
            "\nShared Components:",
            *[f"- {component}" for component in context['shared_components']],
            "\nTechnical Architecture:",
            *[f"- {tech}" for tech in context['technical_architecture']]
        ]
        return "\n".join(sections)

    def _create_element_prompt(self, element: Dict) -> str:
        """Create a detailed prompt for element analysis"""
        # Create a more concise title for long element names
        element_name = element.get("name", "")
        title = element_name
        # Clean up the title by removing special characters and quotes
        title = title.replace('"', '')  # Remove double quotes
        title = title.replace('“', '')  # Remove left double quotes
        title = title.replace('”', '')  # Remove right double quotes
        title = title.replace('‘', '')  # Remove left single quote
        title = title.replace('’', '')  # Remove right single quote
        title = title.strip()  # Remove extra whitespace
        
        # If name is too long, truncate it
        if len(title) > 50:
            title = title[:50] + "..."  # Truncate to 50 chars with ellipsis
        
        return SYSTEM_ELEMENT_PROMPT.format(
            type=element.get("type", ""),
            name=title,
            description=element.get("description", "N/A"),
            properties=self._format_properties(element.get("properties", {}))
        )

    def _format_properties(self, properties: Dict) -> str:
        """Format element properties for the prompt"""
        formatted = []
        for key, value in properties.items():
            if isinstance(value, (dict, list)):
                formatted.append(f"- {key}: {str(value)}")
            else:
                formatted.append(f"- {key}: {value}")
        return "\n".join(formatted)

    def _parse_response(self, response: str, element: Dict) -> DesignAnalysis:
        """Parse the AI response into structured data"""
        try:
            logger.debug(f"Raw AI response:\n{response}")  # Log the raw response for debugging
            logger.debug(f"Element info: {element}")  # Log the element info
            
            # First check if the response contains a valid title
            title_match = re.search(r'TITLE:\s*(.+)', response)
            if title_match:
                title = title_match.group(1).strip()
                if title and len(title) <= 50:
                    logger.debug(f"Found valid title: {title}")
                    data = {'title': title}
                else:
                    logger.warning(f"Invalid title format or length: {title}")
                    data = {'title': f"{element.get('type', 'Element')} - {element.get('name', 'Unnamed Element')[:50]}"}
            else:
                logger.warning("No title found in response, using fallback")
                data = {'title': f"{element.get('type', 'Element')} - {element.get('name', 'Unnamed Element')[:50]}"}
            
            # Split the response into lines for further parsing
            lines = response.split('\n')
            data.update({
                'description': '',
                'user_story': '',
                'acceptance_criteria': [],
                'technical_requirements': [],
                'story_points': 3,
                'priority': 'Medium',
                'type': 'Feature'
            })
            
            current_section = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                elif line.startswith('USER_STORY:'):
                    user_story = line.replace('USER_STORY:', '').strip()
                    if user_story:
                        data['user_story'] = user_story
                    else:
                        logger.warning("Empty user story found in response")
                elif line.startswith('ACCEPTANCE_CRITERIA:'):
                    current_section = 'acceptance_criteria'
                    logger.debug("Starting to parse acceptance criteria")
                elif line.startswith('TECHNICAL_REQUIREMENTS:'):
                    current_section = 'technical_requirements'
                    logger.debug("Starting to parse technical requirements")
                elif line.startswith('POINTS:'):
                    points_text = line.replace('POINTS:', '').strip()
                    points_match = next((char for char in points_text if char.isdigit()), '3')
                    data['story_points'] = int(points_match)
                elif line.startswith('PRIORITY:'):
                    # Extract just the priority level without justification
                    priority_text = line.replace('PRIORITY:', '').strip()
                    priority_words = priority_text.split()
                    if priority_words:
                        data['priority'] = priority_words[0]  # Take first word as priority
                elif line.startswith('TYPE:'):
                    # Extract story type
                    type_text = line.replace('TYPE:', '').strip()
                    data['type'] = type_text if type_text else 'Feature'
                elif line.startswith('-') and current_section:
                    data[current_section].append(line.replace('-', '').strip())
            
            # Validate story points are within acceptable range
            if data['story_points'] not in [1, 2, 3, 5, 8]:
                logger.warning(f"Invalid story points value: {data['story_points']}, defaulting to 3")
                data['story_points'] = 3
                
            # Validate priority is a known value
            valid_priorities = ['Highest', 'High', 'Medium', 'Low']
            if data['priority'] not in valid_priorities:
                logger.warning(f"Invalid priority value: {data['priority']}, defaulting to Medium")
                data['priority'] = 'Medium'
            
            return DesignAnalysis(
                title=data['title'],
                description=data['user_story'],
                user_story=data['user_story'],
                acceptance_criteria=data['acceptance_criteria'],
                technical_requirements=data['technical_requirements'],
                story_points=data['story_points'],
                priority=data['priority'],
                type=data['type']
            )
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            raise

    def _perform_analysis(self, element: dict, product_context: str, template: str) -> DesignAnalysis:
        """
        Perform the core analysis of a design element using AI.
        
        Args:
            element: The design element to analyze
            product_context: The product context for the analysis
            template: The template to use for the analysis
        
        Returns:
            A DesignAnalysis object containing the analysis results
        """
        try:
            # Create prompt with context and element details
            element_prompt = self._create_element_prompt(element)
            
            # Combine context and element prompt
            full_prompt = f"{product_context}\n\n{element_prompt}"
            
            # Get AI response
            # Convert template to string if it's not already
            system_content = template if isinstance(template, str) else str(template)
            
            # Create the chat completion request
            completion = self.client.chat.completions.create(
                model=self.config.get("model", "gpt-3.5-turbo"),
                temperature=self.config.get("temperature", 0.7),
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            # Get the message content from the completion
            message_content = completion.choices[0].message.content
            
            # Parse the response
            return self._parse_response(message_content, element)
            
        except Exception as e:
            logger.error(f"Error performing analysis: {e}")
            raise

    def analyze_element_with_context(self, element: dict, product_context: str) -> DesignAnalysis:
        """
        Analyze a design element with consolidated product context and generate a user story.
        Args:
            element: Trimmed Figma design element
            product_context: Consolidated application context (string or dict)
        Returns:
            Analysis results including story details
        """
        try:
            # Get appropriate template
            template = self.template_manager.get_template(element['type'])
            
            # Create element-specific prompt
            element_prompt = self._create_element_prompt(element)
            
            # Combine context and element prompt
            prompt = f"{product_context}\n\n{element_prompt}"
            
            # Log the prompt being used
            logger.info(f"Using prompt for element {element['name']}:\n{prompt}")
            
            # Perform analysis
            analysis = self._perform_analysis(element, product_context, template)
            logger.debug(f"Parsed analysis: {analysis.dict()}")  # Log parsed analysis
            
            # Enhanced quality check with strict validation
            quality_report = self.quality_checker.check_quality(analysis.dict())
            if not quality_report['passes_threshold']:
                logger.warning(f"Quality issues found: {quality_report['issues']}")
                logger.info(f"Suggestions: {quality_report['suggestions']}")
                
                # Check for mandatory Jira fields
                required_fields = [
                    'title' in analysis.dict() and analysis.title.strip(),
                    'description' in analysis.dict() and analysis.description.strip(),
                    len(analysis.acceptance_criteria) > 0,
                    len(analysis.technical_requirements) > 0
                ]
                
                if not all(required_fields):
                    logger.error("Missing required Jira fields:")
                    if not analysis.title.strip():
                        logger.error("- Missing valid title")
                    if not analysis.description.strip():
                        logger.error("- Missing description")
                    if len(analysis.acceptance_criteria) == 0:
                        logger.error("- Missing acceptance criteria")
                    if len(analysis.technical_requirements) == 0:
                        logger.error("- Missing technical requirements")
                    raise ValueError("Story does not meet Jira quality requirements")
            
            # Record prompt performance
            self.prompt_manager.record_prompt_performance(
                self.prompt_manager.current_version,
                {'quality_score': quality_report['total_score']}
            )
            
            return analysis
        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            raise