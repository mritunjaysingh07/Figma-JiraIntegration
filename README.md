## Figma to Jira Automation
Automate the creation of product-grade Jira stories and epics directly from Figma designs (via Figma API, PDF, or exported JSON). This tool uses GenAI to analyze high-level design elements and generate actionable, business-focused Jira issues.

# Figma to Jira Automation

An automated assistant that extracts design components from Figma (via API or PDF, JSON), analyzes them using AI, and creates corresponding Epics and Stories in Jira. Supports both CLI and webhook (FastAPI) modes for flexible integration.
## To print all types in your current Figma data:
types = set(el.get('type') for el in elements)
print("All Figma element types in this file:", types)

---

## 📁 Code Structure

```
figma_to_jira/
│
├── data/                      # Place your Figma JSON exports here
│   └── sample_figma_data.json
│
├── src/
│   ├── cli.py   # Main CLI entry point
|   |---prompts.py               
│   ├── config.py              # Configuration loader (loads config.yaml)
│   ├── ai_processor.py        # AI logic for story/epic generation
│   ├── pdf_parser.py          # PDF extraction logic
│   └── services/
│       ├── figma_service.py   # Figma API integration
│       └── jira_service.py    # Jira API integration
│
├── app.log                    # Application logs
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🚀 Features

- Extracts all design components from Figma (API) or PDF.
- Supports all Figma node types by default (configurable).
- AI-powered holistic context analysis of the entire design.
- AI-generated user stories, acceptance criteria, and technical requirements for each component.
- Creates Epics and Stories in Jira (project key from config or CLI).
- CLI mode for batch processing.
- FastAPI webhook mode for automation and integration.
- Configurable via YAML for credentials, rate limits, and component filtering.
- Health check endpoint for monitoring.
- Modular, extensible, and production-ready codebase.

---

## Configuration (`src/config.yaml`)

- **Jira**: Project key, credentials, and field mappings.
- **AI**: Model, temperature, OpenAI key, and prompt templates.
- **Figma**: Access token, rate limits, and (optionally) `components_to_analyze`.

---

## How to Use

### 1. **Install dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Configure your credentials**
Edit `src/config.yaml` with your Jira, Figma, and OpenAI credentials.

### 3. **Run in CLI mode**

#### **A. Analyze a local PDF design**
```bash
python src/cli.py --local path/to/design.pdf
```

#### **B. Analyze a Figma design via API**
```bash
python src/cli.py --api YOUR_FIGMA_FILE_ID
>python src/cli.py --api kvVRZ8x8LR6AXe6f6cGtNs 
```

## Json Support
python cli.py --json sample_figma_data.json  

#### **C. Override Jira project key (optional)**
```bash
python src/cli.py --api YOUR_FIGMA_FILE_ID --project YOUR_PROJECT_KEY
```

### 4. **Run as a webhook server (FastAPI)**
```bash
python src/cli.py --webhook
```
- POST to `http://localhost:8000/webhook/jira` with JSON:
    - For Figma: `{"design_id": "YOUR_FIGMA_FILE_ID"}`
    - For PDF: `{"pdf_path": "path/to/design.pdf"}`

---

## Override Jira Project key (Optional)
python src/cli.py --api <FIGMA_FILE_ID> --project <JIRA_PROJECT_KEY>

## 🧠 How It Works

1. **Extracts all design components** from Figma (API) or PDF.
2. **AI analyzes the full design** for holistic context.
3. **AI generates user stories** for each component, using the context.
4. **Creates Epics and Stories in Jira** (project key from config or CLI).
5. **Supports all Figma node types** by default (unless filtered in config).

---

## 📝 Example `config.yaml`

```yaml
jira:
  project_key: "SCRUM"
  url: "https://your-domain.atlassian.net"
  email: "your-email@example.com"
  api_token: "YOUR_JIRA_API_TOKEN"
  fields:
    story_points: "customfield_10016"
    epic_link: "customfield_10014"
    epic_name: "customfield_10011"
    design_link: "customfield_10010"

ai:
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 2000
  openai_api_key: "YOUR_OPENAI_API_KEY"
  prompt_templates:
    story_analysis: "Analyze this design element and create a user story..."
    acceptance_criteria: "Generate acceptance criteria for..."
    technical_requirements: "Generate technical requirements for..."

figma:
  access_token: "YOUR_FIGMA_ACCESS_TOKEN"
  # components_to_analyze:
  #   - "FRAME"
  #   - "COMPONENT"
  #   - "INSTANCE"
  #   - "TEXT"
  #   - "GROUP"
  rate_limit:
    calls_per_minute: 60
    min_delay: 1.0
```

---

## 🩺 Health Check

When running in webhook mode, check:
```
GET http://localhost:8000/health
```
Returns: `{"status": "healthy"}`

---

## 🤝 Contributing

- Fork, branch, and PR as usual.
- Please keep code modular and config-driven.

---

## 📢 Notes

- The AI processor expects a holistic context pass before per-component analysis.
- Jira project key can be set in config or overridden via CLI.
- Figma Id - kvVRZ8x8LR6AXe6f6cGtNs
---

## Application Working (Detailed)
Input Source Selection:
The user can provide a Figma design via API (--api), a local PDF (--local), or a Figma JSON export (--json). The application extracts design elements from the chosen source.

Element Filtering:
The tool automatically filters for high-level, meaningful design elements (such as screens, frames, flows, or components) to avoid generating irrelevant or low-value stories.

Context Generation:
Using GenAI (OpenAI), the application analyzes the overall design to generate a holistic product context. This context summarizes the product’s purpose, main flows, and user goals.

Story Generation:
For each high-level element, the AI generates a detailed user story, acceptance criteria, and technical requirements, always referencing the overall product context for relevance and consistency.

Epic Grouping (Optional):
The tool can group related stories into epics using AI, making backlog management easier.

Jira Issue Creation:
The generated stories (and optionally epics) are automatically created in the specified Jira project. The project key is taken from the config file or can be overridden via CLI.

Modes of Operation:

CLI Mode: For batch processing and one-off runs.
Webhook Mode: Runs a FastAPI server to accept design files and trigger the workflow via HTTP requests.
Logging & Validation:
All actions, including element types and LLM outputs, are logged. Only stories with valid titles are created in Jira, ensuring a clean and actionable backlog.

In summary:
The application transforms high-level Figma design elements into actionable, product-grade Jira stories and epics, using GenAI for context-aware analysis, and automates their creation in Jira for streamlined product development.


##############################################################################

🔄 Application Workflow
1. Input Source Selection

    User Action: Run CLI with --api, --local, or --json
    File: cli.py
    Function:
        extract_elements_from_figma (API)
        extract_elements_from_pdf (PDF)
        extract_elements_from_json (JSON)
Result: Extracts all design elements from the chosen source.

2. Element Filtering

    File: cli.py
    Function: is_high_level_element
Result: Filters for high-level, meaningful elements (screens, frames, flows, components).

3. Product Context Generation

    File: ai_processor.py
    Function: AIProcessor.analyze_application_context
Result: Uses GenAI to generate a holistic product context from the filtered elements.

4. Story Generation

    File: ai_processor.py
    Function: AIProcessor.analyze_element_with_context
Result: For each high-level element, generates a user story, acceptance criteria, and technical requirements using the product context.

5. Epic Grouping (Optional)

    File: ai_processor.py
    Function: AIProcessor.generate_epic_summary
Result: Groups related stories into epics using AI.

6. Jira Issue Creation

    File: jira_service.py
    Function: JiraService.create_story
Result: Creates the generated stories (and optionally epics) in the specified Jira project (project key from config or CLI).

7. Logging & Validation

    Files:
    cli.py (prints/logs element types and LLM outputs)
    ai_processor.py (logs AI analysis and errors)
    app.log (stores logs)
Result: Only stories with valid titles are created in Jira; all actions are logged for traceability.

8. E2E Flow Example (API Source)
User runs:
1.  cli.py loads config and extracts elements using extract_elements_from_figma.
2.  cli.py filters elements with is_high_level_element.
3.  AIProcessor.analyze_application_context generates product context.
4.  For each element, AIProcessor.analyze_element_with_context generates a story.
    (Optional) AIProcessor.generate_epic_summary groups stories into epics.
5.  JiraService.create_story creates issues in Jira.
6.  All steps and outputs are logged.


# Summary Table

Step	                 File(s) & Function(s) Used	                     Purpose
Input Source Selection	cli.py (extract_elements_from_*)	             Extract design elements
Element Filtering	    cli.py (is_high_level_element)	                 Keep only high-level features
Context Generation	    ai_processor.py (analyze_application_context)	  Summarize product for LLM
Story Generation	    ai_processor.py (analyze_element_with_context)	      Generate stories for each feature
Epic Grouping (Optional)	ai_processor.py (generate_epic_summary)	        Group stories into epics
Jira Issue Creation	    services/jira_service.py                        (create_story)	Create issues in Jira
Logging & Validation	cli.py, ai_processor.py, app.log	                Traceability and error handling
