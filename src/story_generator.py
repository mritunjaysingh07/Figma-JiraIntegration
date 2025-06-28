from typing import Dict, List, Any, Optional, Tuple
from loguru import logger
from pydantic import BaseModel
from enum import Enum

from figma_client import FigmaClient, FigmaComponent
from ai_processor import AIProcessor, DesignAnalysis
from jira_client import JiraStory

class StoryType(Enum):
    FEATURE = "Feature"
    ENHANCEMENT = "Enhancement"
    TECHNICAL = "Technical"
    UI_COMPONENT = "UI Component"
    INTEGRATION = "Integration"

class StoryPriority(Enum):
    HIGHEST = "Highest"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class StandardStory(BaseModel):
    """Standard market structure for user stories"""
    title: str
    type: StoryType
    priority: StoryPriority
    business_value: str
    user_story: str
    acceptance_criteria: List[str]
    technical_requirements: List[str]
    dependencies: List[str]
    design_references: List[str]
    story_points: int
    labels: List[str]

class StoryGenerator:
    """Coordinates between Figma, AI, and Jira to generate user stories"""
    
    def __init__(self, figma_client: FigmaClient, ai_processor: AIProcessor, config: Dict):
        self.figma_client = figma_client
        self.ai_processor = ai_processor
        self.config = config
        self.design_context = None

    def generate_stories(self, elements: List[Dict]) -> Tuple[List[JiraStory], List[Dict]]:
        """
        Generate user stories from Figma elements using a standardized approach
        
        Args:
            elements: List of Figma elements to analyze
            
        Returns:
            Tuple of (List of generated Jira stories, List of epics)
        """
        stories = []
        epics = []
        
        try:
            # First, analyze the overall application context
            logger.info("Analyzing overall application context...")
            self.design_context = self.ai_processor.analyze_application_context(elements)
            logger.info(f"Identified application purpose: {self.design_context['core_purpose']}")
            
            # Process JTBD (Jobs To Be Done) and user requirements first
            logger.info("Processing user requirements and JTBD...")
            jtbd_stories = self._process_jtbd_elements(elements)
            if jtbd_stories:
                stories.extend(jtbd_stories)
                # Create epic for JTBD stories
                epics.append({
                    'summary': 'User Requirements Implementation',
                    'description': self._create_epic_description('User Requirements', jtbd_stories),
                    'stories': jtbd_stories
                })
                logger.info(f"Generated {len(jtbd_stories)} stories from JTBD")
            
            # Identify key user flows and features
            user_flows = self._identify_user_flows(elements)
            features = self._identify_features(elements)
            shared_components = self._identify_shared_components(elements)
            
            # Generate stories for user flows first
            logger.info("Generating stories for main user flows...")
            flow_stories = []
            for flow in user_flows:
                story = self._create_flow_story(flow)
                if story:
                    flow_stories.append(story)
                    logger.info(f"Generated story for flow: {flow.get('name', 'Unnamed flow')}")
            
            if flow_stories:
                stories.extend(flow_stories)
                # Create epic for user flows
                epics.append({
                    'summary': 'User Flows Implementation',
                    'description': self._create_epic_description('User Flows', flow_stories),
                    'stories': flow_stories
                })
            
            # Generate stories for features
            logger.info("Generating stories for features...")
            feature_stories = []
            for feature in features:
                story = self._create_feature_story(feature)
                if story:
                    feature_stories.append(story)
                    logger.info(f"Generated story for feature: {feature.get('name', 'Unnamed feature')}")
            
            if feature_stories:
                stories.extend(feature_stories)
                # Create epic for features
                epics.append({
                    'summary': 'Core Features Implementation',
                    'description': self._create_epic_description('Features', feature_stories),
                    'stories': feature_stories
                })
            
            # Generate stories for shared components
            logger.info("Generating stories for shared components...")
            component_stories = []
            for component in shared_components:
                story = self._create_component_story(component)
                if story:
                    component_stories.append(story)
                    logger.info(f"Generated story for component: {component.get('name', 'Unnamed component')}")
            
            if component_stories:
                stories.extend(component_stories)
                # Create epic for shared components
                epics.append({
                    'summary': 'Shared Components Implementation',
                    'description': self._create_epic_description('Shared Components', component_stories),
                    'stories': component_stories
                })
            
            if not stories:
                logger.warning("No stories generated from flows, features, or components")
                # Fallback: Create stories from text elements
                text_stories = self._create_stories_from_text_elements(elements)
                if text_stories:
                    stories.extend(text_stories)
                    # Create epic for text-based stories
                    epics.append({
                        'summary': 'Additional Requirements',
                        'description': self._create_epic_description('Text Requirements', text_stories),
                        'stories': text_stories
                    })
                    logger.info(f"Generated {len(text_stories)} stories from text elements")
            
            logger.info(f"Successfully generated {len(stories)} stories and {len(epics)} epics")
            return stories, epics
            
        except Exception as e:
            logger.error(f"Error generating stories: {e}")
            raise

    def _process_jtbd_elements(self, elements: List[Dict]) -> List[JiraStory]:
        """Process Jobs To Be Done and user requirement text elements"""
        stories = []
        jtbd_elements = []
        
        # Find JTBD and requirement text elements
        for element in elements:
            if element.get('type') == 'TEXT':
                text = element.get('name', '').strip()
                if ('JTBD' in text or 
                    'When I' in text or 
                    'I want to' in text or 
                    'so I can' in text or
                    'so that' in text):
                    jtbd_elements.append(element)
        
        # Process each JTBD element
        for element in jtbd_elements:
            text = element.get('name', '')
            # Split multiple stories if present
            story_texts = text.split('"')
            story_texts = [s.strip() for s in story_texts if s.strip()]
            
            for story_text in story_texts:
                if 'When' in story_text:
                    story = self._create_story_from_jtbd(story_text)
                    if story:
                        stories.append(story)
        
        return stories

    def _create_story_from_jtbd(self, jtbd_text: str) -> Optional[JiraStory]:
        """Create a story from a JTBD (Jobs To Be Done) text"""
        try:
            # Parse JTBD components
            when_part = ""
            want_part = ""
            so_part = ""
            
            # Extract parts using common JTBD format
            if 'When' in jtbd_text:
                parts = jtbd_text.split('When', 1)
                if len(parts) > 1:
                    remaining = parts[1]
                    if 'I want' in remaining:
                        when_part, remaining = remaining.split('I want', 1)
                        if 'so I can' in remaining:
                            want_part, so_part = remaining.split('so I can', 1)
                        elif 'so that' in remaining:
                            want_part, so_part = remaining.split('so that', 1)
            
            # Clean up the parts
            when_part = when_part.strip().strip(',')
            want_part = want_part.strip().strip(',')
            so_part = so_part.strip().strip('.')

            # Generate technical requirements
            tech_reqs = self._generate_technical_requirements_from_jtbd(when_part, want_part, so_part)
            
            # Create the story
            return JiraStory(
                summary=f"Digital Assistant - {want_part[:50]}...",
                description=f"""h2. Business Value
{so_part}

h2. User Story
As a user, I want {want_part}, so that {so_part}

h2. Technical Requirements
{self._format_list(tech_reqs)}

h2. Acceptance Criteria
{self._format_list(self._generate_acceptance_criteria_from_jtbd(when_part, want_part, so_part), use_numbers=True)}""",
                issue_type="Story",  # Using standard "Story" type
                story_points=self._estimate_story_points_from_jtbd(want_part),
                acceptance_criteria=self._generate_acceptance_criteria_from_jtbd(when_part, want_part, so_part),
                technical_requirements=tech_reqs,
                labels=["digital-assistant", "jtbd", f"priority-{self._determine_priority_from_jtbd(when_part, want_part).value.lower()}"],
                components=[],
                design_link="",
                priority=self._determine_priority_from_jtbd(when_part, want_part).value,
                business_value=so_part,
                dependencies=[]
            )
            
        except Exception as e:
            logger.error(f"Error creating story from JTBD: {e}")
            return None

    def _generate_acceptance_criteria_from_jtbd(self, when_part: str, want_part: str, so_part: str) -> List[str]:
        """Generate acceptance criteria from JTBD components"""
        criteria = [
            f"Given {when_part}\nWhen the user activates the digital assistant\nThen the system should handle the call automatically",
            f"Given the digital assistant is handling a call\nWhen {want_part}\nThen {so_part}",
            "Given the digital assistant is on a call\nWhen a human representative becomes available\nThen the system should notify the user immediately",
            "Given the system is handling a call\nWhen the user wants to check the call status\nThen they should see real-time status updates",
            "Given a call is in progress\nWhen the user needs to multitask\nThen they should be able to use their device normally"
        ]
        return criteria

    def _generate_technical_requirements_from_jtbd(self, when_part: str, want_part: str, so_part: str) -> List[str]:
        """Generate technical requirements from JTBD components"""
        requirements = [
            "Voice Recognition: Implement AI-powered voice recognition to detect human vs automated responses",
            "Call Management: Develop system to handle phone calls and navigate automated systems",
            "Background Processing: Enable background operation for multitasking",
            "Real-time Updates: Implement status tracking and notification system",
            "User Interface: Create intuitive interface for call monitoring and control"
        ]
        return requirements

    def _estimate_story_points_from_jtbd(self, want_part: str) -> int:
        """Estimate story points based on JTBD complexity"""
        if 'call' in want_part.lower() and 'manage' in want_part.lower():
            return 8  # Complex call management
        elif 'notification' in want_part.lower() or 'status' in want_part.lower():
            return 3  # Moderate complexity
        else:
            return 5  # Default for standard features

    def _determine_priority_from_jtbd(self, when_part: str, want_part: str) -> StoryPriority:
        """Determine priority based on JTBD context"""
        # Convert to lowercase for easier matching
        when_lower = when_part.lower()
        want_lower = want_part.lower()
        
        # Define priority patterns specific to digital assistant
        highest_patterns = [
            ('call', 'manage'),
            ('call', 'handle'),
            ('voice', 'detect'),
            ('human', 'detect'),
            ('automated', 'system')
        ]
        
        high_patterns = [
            ('notification', ''),
            ('alert', ''),
            ('status', 'update'),
            ('real-time', ''),
            ('background', ''),
            ('multitask', '')
        ]
        
        medium_patterns = [
            ('settings', ''),
            ('configure', ''),
            ('customize', ''),
            ('preference', '')
        ]
        
        # Check for highest priority patterns
        for pattern in highest_patterns:
            if pattern[0] in want_lower and (not pattern[1] or pattern[1] in want_lower):
                return StoryPriority.HIGHEST
        
        # Check for high priority patterns
        for pattern in high_patterns:
            if pattern[0] in want_lower and (not pattern[1] or pattern[1] in want_lower):
                return StoryPriority.HIGH
        
        # Check for medium priority patterns
        for pattern in medium_patterns:
            if pattern[0] in want_lower and (not pattern[1] or pattern[1] in want_lower):
                return StoryPriority.MEDIUM
        
        # Default priority
        return StoryPriority.LOW

    def _create_stories_from_text_elements(self, elements: List[Dict]) -> List[JiraStory]:
        """Create stories from text elements as a fallback"""
        stories = []
        
        for element in elements:
            if element.get('type') == 'TEXT':
                text = element.get('name', '').strip()
                if text and not text.startswith('JTBD') and len(text) > 10:
                    story = self._create_story_from_text(element)
                    if story:
                        stories.append(story)
        
        return stories

    def _identify_user_flows(self, elements: List[Dict]) -> List[Dict]:
        """Identify main user flows from design elements"""
        flows = []
        current_flow = None
        
        # Sort elements by position and grouping
        sorted_elements = self._sort_elements_by_flow(elements)
        
        for element in sorted_elements:
            if self._is_flow_start(element):
                if current_flow:
                    flows.append(current_flow)
                current_flow = {
                    'name': element.get('name', ''),
                    'elements': [],
                    'entry_point': element
                }
            
            if current_flow:
                current_flow['elements'].append(element)
                
            if self._is_flow_end(element) and current_flow:
                flows.append(current_flow)
                current_flow = None
        
        if current_flow:  # Add last flow if exists
            flows.append(current_flow)
            
        return flows

    def _sort_elements_by_flow(self, elements: List[Dict]) -> List[Dict]:
        """Sort elements based on their position and grouping in the design"""
        # First, group elements by their parent frame/group
        grouped_elements = {}
        standalone_elements = []
        
        for element in elements:
            parent_id = element.get('parent_id')
            if parent_id:
                if parent_id not in grouped_elements:
                    grouped_elements[parent_id] = []
                grouped_elements[parent_id].append(element)
            else:
                standalone_elements.append(element)
        
        # Sort elements within each group by position (top to bottom, left to right)
        for group in grouped_elements.values():
            group.sort(key=lambda x: (
                x.get('position', {}).get('y', 0),
                x.get('position', {}).get('x', 0)
            ))
        
        # Combine all elements in the correct order
        sorted_elements = []
        
        # Add frame/group elements first
        frame_elements = [e for e in elements if e.get('type') in ['FRAME', 'GROUP']]
        frame_elements.sort(key=lambda x: (
            x.get('position', {}).get('y', 0),
            x.get('position', {}).get('x', 0)
        ))
        
        # Add elements from each frame/group
        for frame in frame_elements:
            frame_id = frame.get('id')
            if frame_id in grouped_elements:
                sorted_elements.extend(grouped_elements[frame_id])
        
        # Add standalone elements
        sorted_elements.extend(standalone_elements)
        
        return sorted_elements

    def _is_flow_start(self, element: Dict) -> bool:
        """Determine if an element represents the start of a user flow"""
        element_name = element.get('name', '').lower()
        element_type = element.get('type', '').upper()
        
        # Check element name for flow start indicators
        start_indicators = [
            'start', 'entry', 'begin', 'landing', 'home',
            'login', 'signup', 'onboarding', 'initial'
        ]
        
        # Check if element is a frame/screen and has start indicators
        is_container = element_type in ['FRAME', 'GROUP', 'SECTION']
        has_start_name = any(indicator in element_name for indicator in start_indicators)
        
        # Check for UI elements that typically start flows
        is_entry_point = (
            element_type in ['INSTANCE', 'COMPONENT'] and
            any(indicator in element_name for indicator in ['button', 'link', 'nav', 'menu'])
        )
        
        return (is_container and has_start_name) or is_entry_point

    def _is_flow_end(self, element: Dict) -> bool:
        """Determine if an element represents the end of a user flow"""
        element_name = element.get('name', '').lower()
        element_type = element.get('type', '').upper()
        
        # Check element name for flow end indicators
        end_indicators = [
            'end', 'finish', 'complete', 'success', 'confirmation',
            'thank you', 'done', 'final', 'submit'
        ]
        
        # Check if element is a frame/screen and has end indicators
        is_container = element_type in ['FRAME', 'GROUP', 'SECTION']
        has_end_name = any(indicator in element_name for indicator in end_indicators)
        
        # Check for UI elements that typically end flows
        is_end_point = (
            element_type in ['INSTANCE', 'COMPONENT'] and
            any(indicator in element_name for indicator in ['submit', 'confirm', 'finish'])
        )
        
        return (is_container and has_end_name) or is_end_point

    def _identify_features(self, elements: List[Dict]) -> List[Dict]:
        """Identify distinct features from design elements"""
        features = []
        current_feature = None
        
        # Group elements by their parent frame/component
        grouped_elements = {}
        for element in elements:
            parent_id = element.get('parent_id')
            if parent_id:
                if parent_id not in grouped_elements:
                    grouped_elements[parent_id] = []
                grouped_elements[parent_id].append(element)
        
        # Identify features from frames and groups
        for element in elements:
            if element.get('type') in ['FRAME', 'GROUP', 'COMPONENT_SET']:
                feature_name = self._extract_feature_name(element)
                if feature_name:
                    feature = {
                        'name': feature_name,
                        'main_element': element,
                        'elements': grouped_elements.get(element.get('id'), []),
                        'description': element.get('description', '')
                    }
                    features.append(feature)
        
        return features

    def _identify_shared_components(self, elements: List[Dict]) -> List[Dict]:
        """Identify shared/reusable components from design elements"""
        components = []
        component_instances = {}
        
        # First pass: identify component instances
        for element in elements:
            if element.get('type') == 'INSTANCE':
                component_id = element.get('component_id')
                if component_id:
                    if component_id not in component_instances:
                        component_instances[component_id] = []
                    component_instances[component_id].append(element)
        
        # Second pass: create shared component entries
        for element in elements:
            if element.get('type') == 'COMPONENT':
                component_id = element.get('id')
                if component_id in component_instances and len(component_instances[component_id]) > 1:
                    component = {
                        'name': element.get('name', ''),
                        'main_element': element,
                        'instances': component_instances[component_id],
                        'description': element.get('description', ''),
                        'usage_count': len(component_instances[component_id])
                    }
                    components.append(component)
        
        return components

    def _extract_feature_name(self, element: Dict) -> str:
        """Extract a clean feature name from an element"""
        name = element.get('name', '').strip()
        
        # Remove common prefixes/suffixes
        prefixes = ['feature:', 'feature -', 'module:', 'section:']
        suffixes = ['section', 'module', 'feature', 'component']
        
        name_lower = name.lower()
        for prefix in prefixes:
            if name_lower.startswith(prefix):
                name = name[len(prefix):].strip()
                break
                
        for suffix in suffixes:
            if name_lower.endswith(suffix):
                name = name[:-len(suffix)].strip()
                break
        
        return name.title()

    def _create_standardized_story(self, analysis: DesignAnalysis, context: Dict) -> StandardStory:
        """Create a standardized story structure"""
        return StandardStory(
            title=analysis.title,
            type=self._determine_story_type(analysis, context),
            priority=self._determine_priority(analysis, context),
            business_value=self._extract_business_value(analysis),
            user_story=analysis.user_story,
            acceptance_criteria=self._standardize_acceptance_criteria(analysis.acceptance_criteria),
            technical_requirements=self._standardize_technical_requirements(analysis.technical_requirements),
            dependencies=self._identify_dependencies(analysis, context),
            design_references=self._get_design_references(context),
            story_points=analysis.story_points,
            labels=self._generate_standard_labels(analysis, context)
        )

    def _create_jira_story(self, standard_story: StandardStory) -> JiraStory:
        """Convert standardized story to Jira format"""
        description = f"""h2. Business Value
{standard_story.business_value}

h2. User Story
{standard_story.user_story}

h2. Technical Requirements
{self._format_list(standard_story.technical_requirements)}

h2. Acceptance Criteria
{self._format_list(standard_story.acceptance_criteria, use_numbers=True)}"""

        if standard_story.dependencies:
            description += f"\n\nh2. Dependencies\n{self._format_list(standard_story.dependencies)}"

        if standard_story.design_references:
            description += f"\n\nh2. Design References\n{self._format_list(standard_story.design_references)}"

        return JiraStory(
            summary=standard_story.title,
            description=description,
            issue_type=standard_story.type.value,
            story_points=standard_story.story_points,
            acceptance_criteria=standard_story.acceptance_criteria,
            technical_requirements=standard_story.technical_requirements,
            labels=standard_story.labels,
            components=[],
            design_link=", ".join(standard_story.design_references),
            priority=standard_story.priority.value,
            business_value=standard_story.business_value,
            dependencies=standard_story.dependencies
        )

    def _standardize_acceptance_criteria(self, criteria: List[str]) -> List[str]:
        """Standardize acceptance criteria format"""
        standardized = []
        for criterion in criteria:
            # Ensure each criterion follows Given-When-Then format
            if not any(pattern in criterion.lower() for pattern in ['given', 'when', 'then']):
                criterion = f"Given the user is on the relevant screen\nWhen {criterion}\nThen the system should respond appropriately"
            standardized.append(criterion)
        return standardized

    def _standardize_technical_requirements(self, requirements: List[str]) -> List[str]:
        """Standardize technical requirements format"""
        categories = {
            'UI': [],
            'Performance': [],
            'Security': [],
            'Integration': [],
            'Testing': []
        }
        
        for req in requirements:
            categorized = False
            for category in categories.keys():
                if category.lower() in req.lower():
                    categories[category].append(req)
                    categorized = True
                    break
            if not categorized:
                categories['UI'].append(req)
        
        standardized = []
        for category, reqs in categories.items():
            if reqs:
                standardized.append(f"{category}:")
                standardized.extend(reqs)
        
        return standardized

    def _determine_story_type(self, analysis: DesignAnalysis, context: Dict) -> StoryType:
        """Determine appropriate story type based on analysis"""
        if "integration" in analysis.title.lower():
            return StoryType.INTEGRATION
        elif "component" in analysis.title.lower():
            return StoryType.UI_COMPONENT
        elif "technical" in analysis.title.lower():
            return StoryType.TECHNICAL
        elif "enhance" in analysis.title.lower():
            return StoryType.ENHANCEMENT
        else:
            return StoryType.FEATURE

    def _extract_business_value(self, analysis: DesignAnalysis) -> str:
        """Extract business value from analysis"""
        # Extract the "so that" part from user story
        if "so that" in analysis.user_story.lower():
            return analysis.user_story.split("so that")[-1].strip()
        return "Implements required functionality based on design specifications"

    def _generate_standard_labels(self, analysis: DesignAnalysis, context: Dict) -> List[str]:
        """Generate standardized labels"""
        labels = ["figma-generated"]
        
        # Add type-based label
        story_type = getattr(analysis, 'type', 'Feature').lower()
        labels.append(f"type-{story_type}")
        
        # Add scope-based label
        if "frontend" in str(analysis.technical_requirements).lower():
            labels.append("frontend")
        if "backend" in str(analysis.technical_requirements).lower():
            labels.append("backend")
        
        # Add complexity-based label
        if analysis.story_points <= 2:
            labels.append("complexity-low")
        elif analysis.story_points <= 5:
            labels.append("complexity-medium")
        else:
            labels.append("complexity-high")
            
        return labels

    def _create_epic_description(self, feature: str, stories: List[JiraStory]) -> str:
        """Create a comprehensive epic description"""
        description = [
            f"h2. {feature} Implementation",
            "",
            "This epic covers the implementation of the following user stories:",
            ""
        ]
        
        # Group stories by type
        stories_by_type = {}
        for story in stories:
            story_type = story.issue_type
            if story_type not in stories_by_type:
                stories_by_type[story_type] = []
            stories_by_type[story_type].append(story)
        
        # Add stories grouped by type
        for story_type, type_stories in stories_by_type.items():
            description.append(f"h3. {story_type}s")
            for story in type_stories:
                description.append(f"* {story.summary}")
            description.append("")
        
        return "\n".join(description)

    def _identify_dependencies(self, analysis: DesignAnalysis, context: Dict) -> List[str]:
        """
        Identify dependencies for a story based on analysis and context
        
        Args:
            analysis: Design analysis results
            context: Additional context information
            
        Returns:
            List of dependency descriptions
        """
        dependencies = []
        
        # Check for component dependencies
        if 'component_instances' in context:
            for instance in context.get('component_instances', []):
                if instance.get('name'):
                    dependencies.append(f"Requires component: {instance['name']}")
        
        # Check for feature dependencies
        if 'feature_elements' in context:
            for element in context.get('feature_elements', []):
                if element.get('type') == 'INSTANCE':
                    dependencies.append(f"Requires feature: {element.get('name', 'Unknown')}")
        
        # Check for flow dependencies
        if 'flow_elements' in context:
            prev_element = None
            for element in context.get('flow_elements', []):
                if prev_element:
                    dependencies.append(f"Requires completion of: {prev_element.get('name', 'Unknown')}")
                prev_element = element
        
        # Add technical dependencies from analysis
        if hasattr(analysis, 'technical_requirements'):
            for req in analysis.technical_requirements:
                if any(keyword in req.lower() for keyword in ['requires', 'depends', 'after', 'before']):
                    dependencies.append(req)
        
        return list(set(dependencies))  # Remove duplicates

    def _determine_priority(self, analysis: DesignAnalysis, context: Dict) -> StoryPriority:
        """Determine the priority of a story based on analysis and context"""
        # Get the story content in lowercase for easier matching
        title_lower = analysis.title.lower()
        description_lower = analysis.description.lower()
        user_story_lower = analysis.user_story.lower()
        
        # Check for highest priority indicators
        highest_priority_indicators = [
            'core functionality',
            'critical',
            'essential',
            'main flow',
            'primary',
            'call management',
            'voice recognition',
            'human detection',
            'automated system navigation'
        ]
        
        # Check for high priority indicators
        high_priority_indicators = [
            'user experience',
            'notification',
            'alert',
            'status update',
            'feedback',
            'real-time',
            'background process'
        ]
        
        # Check for medium priority indicators
        medium_priority_indicators = [
            'enhancement',
            'improvement',
            'optimization',
            'settings',
            'configuration',
            'preference'
        ]
        
        # Check content against priority indicators
        content = f"{title_lower} {description_lower} {user_story_lower}"
        
        # Determine priority based on content and technical requirements
        if any(indicator in content for indicator in highest_priority_indicators):
            return StoryPriority.HIGHEST
        elif any(indicator in content for indicator in high_priority_indicators):
            return StoryPriority.HIGH
        elif any(indicator in content for indicator in medium_priority_indicators):
            return StoryPriority.MEDIUM
        else:
            return StoryPriority.LOW 

    def _create_flow_story(self, flow: Dict) -> JiraStory:
        """Create a story for a user flow"""
        # Extract flow information
        flow_name = flow.get('name', '')
        elements = flow.get('elements', [])
        entry_point = flow.get('entry_point', {})
        
        # Create a comprehensive analysis of the flow
        flow_analysis = {
            'type': 'FLOW',
            'name': flow_name,
            'description': f"User flow starting from {entry_point.get('name', '')}",
            'properties': {
                'elements': [e.get('name', '') for e in elements],
                'entry_point': entry_point.get('name', ''),
                'flow_type': 'user_journey'
            }
        }
        
        # Get AI analysis for the flow
        analysis = self.ai_processor.analyze_element(flow_analysis)
        
        # Create standardized story
        standard_story = self._create_standardized_story(analysis, {
            'flow_elements': elements,
            'entry_point': entry_point,
            'context': self.design_context
        })
        
        # Convert to Jira story with standard type
        return JiraStory(
            summary=standard_story.title,
            description=self._create_story_description(standard_story),
            issue_type="Story",  # Using standard "Story" type
            story_points=standard_story.story_points,
            acceptance_criteria=standard_story.acceptance_criteria,
            technical_requirements=standard_story.technical_requirements,
            labels=standard_story.labels + ["user-flow"],
            components=[],
            design_link="",
            priority=standard_story.priority.value,
            business_value=standard_story.business_value,
            dependencies=standard_story.dependencies
        )

    def _create_story_description(self, story: StandardStory) -> str:
        """Create a standardized story description"""
        description = f"""h2. Business Value
{story.business_value}

h2. User Story
{story.user_story}

h2. Technical Requirements
{self._format_list(story.technical_requirements)}

h2. Acceptance Criteria
{self._format_list(story.acceptance_criteria, use_numbers=True)}"""

        if story.dependencies:
            description += f"\n\nh2. Dependencies\n{self._format_list(story.dependencies)}"

        if story.design_references:
            description += f"\n\nh2. Design References\n{self._format_list(story.design_references)}"

        return description

    def _create_feature_story(self, feature: Dict) -> JiraStory:
        """Create a story for a feature"""
        # Extract feature information
        feature_name = feature.get('name', '')
        main_element = feature.get('main_element', {})
        elements = feature.get('elements', [])
        
        # Create feature analysis
        feature_analysis = {
            'type': 'FEATURE',
            'name': feature_name,
            'description': feature.get('description', ''),
            'properties': {
                'elements': [e.get('name', '') for e in elements],
                'main_element': main_element.get('name', ''),
                'feature_type': self._determine_feature_type(main_element)
            }
        }
        
        # Get AI analysis for the feature
        analysis = self.ai_processor.analyze_element(feature_analysis)
        
        # Create standardized story
        standard_story = self._create_standardized_story(analysis, {
            'feature_elements': elements,
            'main_element': main_element,
            'context': self.design_context
        })
        
        # Convert to Jira story
        return self._create_jira_story(standard_story)

    def _create_component_story(self, component: Dict) -> JiraStory:
        """Create a story for a shared component"""
        # Extract component information
        component_name = component.get('name', '')
        main_element = component.get('main_element', {})
        instances = component.get('instances', [])
        
        # Create component analysis
        component_analysis = {
            'type': 'COMPONENT',
            'name': component_name,
            'description': component.get('description', ''),
            'properties': {
                'instances': len(instances),
                'usage_locations': [i.get('name', '') for i in instances],
                'component_type': self._determine_component_type(main_element)
            }
        }
        
        # Get AI analysis for the component
        analysis = self.ai_processor.analyze_element(component_analysis)
        
        # Create standardized story
        standard_story = self._create_standardized_story(analysis, {
            'component_instances': instances,
            'main_element': main_element,
            'context': self.design_context
        })
        
        # Convert to Jira story
        return self._create_jira_story(standard_story)

    def _determine_feature_type(self, element: Dict) -> str:
        """Determine the type of feature based on the element"""
        element_name = element.get('name', '').lower()
        
        if any(keyword in element_name for keyword in ['call', 'voice', 'audio']):
            return 'call_management'
        elif any(keyword in element_name for keyword in ['ai', 'assistant', 'automation']):
            return 'ai_assistant'
        elif any(keyword in element_name for keyword in ['user', 'profile', 'account']):
            return 'user_management'
        elif any(keyword in element_name for keyword in ['settings', 'config', 'preferences']):
            return 'configuration'
        else:
            return 'core_feature'

    def _determine_component_type(self, element: Dict) -> str:
        """Determine the type of component based on the element"""
        element_name = element.get('name', '').lower()
        
        if any(keyword in element_name for keyword in ['button', 'action']):
            return 'action_component'
        elif any(keyword in element_name for keyword in ['input', 'field', 'form']):
            return 'input_component'
        elif any(keyword in element_name for keyword in ['card', 'container', 'box']):
            return 'container_component'
        elif any(keyword in element_name for keyword in ['icon', 'image', 'visual']):
            return 'visual_component'
        else:
            return 'ui_component'

    def _create_story_from_text(self, text_element: Dict) -> JiraStory:
        """Create a story from a text element that contains requirements"""
        text = text_element.get('name', '')
        
        # Get AI analysis of the text element
        analysis = self.ai_processor.analyze_element({
            'type': 'TEXT',
            'name': text,
            'description': 'Text requirement from Figma design',
            'properties': {
                'content': text,
                'type': 'requirement'
            }
        })
        
        # Create story description with proper Jira formatting
        description = f"""h2. User Story
{analysis.user_story}

h2. Original Requirement
{text}

h2. Technical Requirements
{self._format_list(analysis.technical_requirements)}

h2. Acceptance Criteria
{self._format_list(analysis.acceptance_criteria, use_numbers=True)}"""
        
        # Create Jira story with improved structure
        story = JiraStory(
            summary=analysis.title,
            description=description,
            issue_type="Story",
            story_points=analysis.story_points,
            acceptance_criteria=analysis.acceptance_criteria,
            labels=["figma-generated", "requirement"],
            components=[],
            design_link=""
        )
        
        return story

    def _create_story_from_element(self, element: Dict) -> JiraStory:
        """Create a story from a Figma element"""
        # Get AI analysis of the element
        analysis = self.ai_processor.analyze_element(element)
        
        # Create story description with proper Jira formatting
        description = f"""h2. User Story
{analysis.user_story}

h2. Design Element Details
* Type: {element.get('type')}
* Name: {element.get('name')}

h2. Element Properties
{self._format_element_properties(element)}

h2. Technical Requirements
{self._format_list(analysis.technical_requirements)}

h2. Acceptance Criteria
{self._format_list(analysis.acceptance_criteria, use_numbers=True)}"""
        
        # Create Jira story with improved structure
        story = JiraStory(
            summary=analysis.title,
            description=description,
            issue_type="Story",
            story_points=analysis.story_points,
            acceptance_criteria=analysis.acceptance_criteria,
            labels=["figma-generated", f"element-{element.get('type', '').lower()}", "ui-component"],
            components=[],
            design_link=""
        )
        
        return story

    def _format_element_properties(self, element: Dict) -> str:
        """Format element properties for description"""
        properties = element.get('properties', {})
        formatted = []
        
        # Add basic properties
        if 'constraints' in properties:
            formatted.append(f"* Constraints: {properties['constraints']}")
        if 'layout' in properties:
            formatted.append(f"* Layout: {properties['layout']}")
        
        # Add text-specific properties
        if element.get('type') == 'TEXT' and 'characters' in properties:
            formatted.append(f"* Text Content: {properties['characters']}")
        
        # Add style properties
        if 'styles' in properties and properties['styles']:
            formatted.append("* Styles:")
            for style_key, style_value in properties['styles'].items():
                formatted.append(f"  - {style_key}: {style_value}")
        
        # Add visual properties
        if 'fills' in properties and properties['fills']:
            formatted.append("* Fills:")
            for fill in properties['fills']:
                formatted.append(f"  - Type: {fill.get('type')}")
        
        if 'strokes' in properties and properties['strokes']:
            formatted.append("* Strokes:")
            for stroke in properties['strokes']:
                formatted.append(f"  - Type: {stroke.get('type')}")
        
        return "\n".join(formatted) if formatted else "No specific properties found"

    def _format_list(self, items: List[str], use_numbers: bool = False) -> str:
        """Format a list of items for Jira markup"""
        if not items:
            return "No items specified"
            
        formatted = []
        for i, item in enumerate(items, 1):
            if use_numbers:
                formatted.append(f"# {item}")
            else:
                formatted.append(f"* {item}")
        
        return "\n".join(formatted)

    def group_related_stories(self, stories: List[JiraStory]) -> Dict[str, List[JiraStory]]:
        """Group related stories together"""
        groups = {}
        
        for story in stories:
            # Use element type as group key
            group_key = story.labels[1] if len(story.labels) > 1 else "misc"
            
            if group_key not in groups:
                groups[group_key] = []
            
            groups[group_key].append(story)
        
        return groups

    def generate_epic(self, stories: List[JiraStory]) -> Dict:
        """Generate an epic for a group of related stories"""
        try:
            # Extract story summaries
            summaries = [story.summary for story in stories]
            
            # Create epic summary
            epic_summary = "Implement Figma Design Components"
            
            # Create epic description
            description = ["h2. Design Implementation Epic", "", "This epic covers the implementation of design elements from Figma.", "", "h2. Included Stories"]
            for story in stories:
                description.append(f"* {story.summary}")
            
            return {
                "summary": epic_summary,
                "description": "\n".join(description)
            }
            
        except Exception as e:
            logger.error(f"Error generating epic: {e}")
            raise

    def _link_related_stories(self, stories: List[JiraStory]) -> List[JiraStory]:
        """Link related stories based on dependencies and relationships"""
        # Create a map of stories by their summaries for easy lookup
        story_map = {story.summary: story for story in stories}
        
        for story in stories:
            related_stories = []
            
            # Extract technical requirements from description
            tech_reqs = self._extract_technical_requirements(story.description)
            
            # Find related stories based on technical requirements
            for req in tech_reqs:
                for other_story in stories:
                    if other_story != story:
                        # Check if this requirement is related to other story's content
                        other_tech_reqs = self._extract_technical_requirements(other_story.description)
                        if any(req.lower() in other_req.lower() for other_req in other_tech_reqs):
                            related_stories.append(other_story.summary)
            
            # Find related stories based on acceptance criteria
            for criterion in story.acceptance_criteria:
                for other_story in stories:
                    if other_story != story and other_story.summary not in related_stories:
                        # Check if this criterion is related to other story's criteria
                        if any(criterion.lower() in other_criterion.lower() 
                              for other_criterion in other_story.acceptance_criteria):
                            related_stories.append(other_story.summary)
            
            # Update story description with related stories section if any found
            if related_stories:
                story.dependencies = related_stories
                if not story.description.endswith('\n\n'):
                    story.description += '\n\n'
                story.description += "h2. Related Stories\n"
                for related_story in related_stories:
                    story.description += f"* {related_story}\n"
        
        return stories

    def _extract_technical_requirements(self, description: str) -> List[str]:
        """Extract technical requirements from story description"""
        requirements = []
        
        # Find the technical requirements section
        if 'h2. Technical Requirements' in description:
            tech_section = description.split('h2. Technical Requirements')[1]
            # Get content until the next section or end
            if 'h2.' in tech_section:
                tech_section = tech_section.split('h2.')[0]
            
            # Extract individual requirements
            for line in tech_section.strip().split('\n'):
                line = line.strip()
                if line and line.startswith('*'):
                    requirements.append(line[1:].strip())
                elif line and ':' in line:
                    requirements.append(line.strip())
        
        return requirements

    def _get_design_references(self, context: Dict) -> List[str]:
        """
        Get design reference information from context
        
        Args:
            context: Context information containing design references
            
        Returns:
            List of design reference descriptions
        """
        references = []
        
        # Add main element reference if present
        if 'main_element' in context:
            element = context['main_element']
            if element:
                references.append(f"Main component: {element.get('name', 'Unknown')} ({element.get('id', 'No ID')})")
        
        # Add component instances if present
        if 'component_instances' in context:
            for instance in context.get('component_instances', []):
                if instance.get('name'):
                    references.append(f"Instance: {instance['name']} ({instance.get('id', 'No ID')})")
        
        # Add flow elements if present
        if 'flow_elements' in context:
            for element in context.get('flow_elements', []):
                if element.get('name'):
                    references.append(f"Flow element: {element['name']} ({element.get('id', 'No ID')})")
        
        return references 