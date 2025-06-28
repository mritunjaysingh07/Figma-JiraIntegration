CONTEXT_ANALYSIS_PROMPT = """You are an expert in analyzing digital product designs. Please analyze the following design elements and provide a structured overview in the exact format shown below:

Core Purpose: [Brief description of the application's main purpose]

Target Users:
- [User type 1]
- [User type 2]

Key Features:
- [Feature 1]
- [Feature 2]

User Flows:
- [Flow 1]
- [Flow 2]

Shared Components:
- [Component 1]
- [Component 2]

Technical Architecture:
- [Architecture element 1]
- [Architecture element 2]

Please ensure your response follows this exact structure and format."""

SYSTEM_CONTEXT_PROMPT = """You are an expert in analyzing digital product designs. Please analyze the following design elements and provide a structured overview in the exact format shown below:

Core Purpose: [Brief description of the application's main purpose]

Target Users:
- [User type 1]
- [User type 2]

Key Features:
- [Feature 1]
- [Feature 2]

User Flows:
- [Flow 1]
- [Flow 2]

Shared Components:
- [Component 1]
- [Component 2]

Technical Architecture:
- [Architecture element 1]
- [Architecture element 2]

Please ensure your response follows this exact structure and format."""

SYSTEM_ELEMENT_PROMPT = """You are an expert in analyzing digital product designs. Please analyze the following design element and provide a structured analysis in the exact format shown below:

Type: {type}
Name: {name}
Description: {description}

Properties:
{properties}

Please analyze this element and provide the following information:

# Required Fields - Must be present and non-empty:
TITLE: [Brief, clear title for the story] (Required, must be 1-50 characters)
USER_STORY: [User story in the format: As a [user], I want [feature] so that [benefit]] (Required)

# Optional Fields - Please provide if relevant:
ACCEPTANCE_CRITERIA:
- [Criteria 1]
- [Criteria 2]
TECHNICAL_REQUIREMENTS:
- [Requirement 1]
- [Requirement 2]

# Estimation Fields:
POINTS: [Estimate story points (1, 2, 3, 5, 8)] (Optional, default 3)
PRIORITY: [Priority level (Highest, High, Medium, Low)] (Optional, default Medium)
TYPE: [Story type (Feature, Bug, Task, etc.)] (Optional, default Feature)

Important Notes:
1. The TITLE must be between 1-50 characters long.
2. The USER_STORY must follow the format: As a [user], I want [feature] so that [benefit].
3. All responses must be in English.
4. Use clear, concise language.
5. Do not include any HTML or markdown formatting.

Please ensure your response follows this exact structure and format. If you cannot provide a valid title or user story, please say so explicitly."""

USER_ELEMENT_PROMPT = """Analyze the following design element and generate a user story:

Element Details:
Name: {name}
Type: {type}
Description: {description}
Properties: {properties}

Please generate a user story that captures:
1. User perspective and goals
2. Specific actions and interactions
3. Expected outcomes and success criteria
4. Any technical considerations

Format the user story in a clear, concise manner."""

SYSTEM_EPIC_PROMPT = """You are an expert in generating comprehensive epic summaries for digital products. Your task is to create a cohesive epic summary based on multiple components.

Components:
{components}

Please generate an epic summary that:
1. Captures the overall theme and purpose
2. Identifies key features and functionality
3. Establishes clear scope and boundaries
4. Provides context for implementation
5. Highlights potential challenges and considerations

Format the summary in a clear, structured manner."""

SELECTED_PROMPT = """You are an expert in selecting the most appropriate prompt for a given design element. Your task is to analyze the element and determine which prompt to use.

Element Details:
Name: {name}
Type: {type}
Description: {description}
Properties: {properties}

Please select the most appropriate prompt from the following options:
1. Context Analysis
2. System Context
3. System Element
4. User Element
5. Epic Summary

Provide a clear justification for your selection."""
