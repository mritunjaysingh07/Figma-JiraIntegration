from typing import Dict, List
import PyPDF2
import re
from loguru import logger

class PDFParser:
    """Parse PDF files to extract Figma design elements for LLM processing."""

    ELEMENT_HEADER_REGEX = re.compile(
        r"^(Screen|Component|Frame|Group|Instance|Text|Section|Page)[:\- ]+(.*)", re.IGNORECASE
    )
    DESCRIPTION_REGEX = re.compile(r"^(Description|Desc)[:\- ]+(.*)", re.IGNORECASE)
    PROPERTY_REGEX = re.compile(r"^([A-Za-z0-9 _\-]+)[:\- ]+(.+)", re.IGNORECASE)

    def parse_pdf(self, pdf_path: str) -> List[Dict]:
        elements = []
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    text = page.extract_text()
                    if not text:
                        continue
                    lines = text.split('\n')
                    current_element = None
                    last_key = None
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        # Detect element headers
                        header_match = self.ELEMENT_HEADER_REGEX.match(line)
                        if header_match:
                            if current_element:
                                elements.append(current_element)
                            element_type = header_match.group(1).upper()
                            name = header_match.group(2).strip()
                            current_element = {
                                "type": element_type,
                                "name": name,
                                "description": "",
                                "properties": {},
                                "page": page_num
                            }
                            last_key = None
                            continue
                        # Description line
                        if current_element:
                            desc_match = self.DESCRIPTION_REGEX.match(line)
                            if desc_match:
                                current_element["description"] = desc_match.group(2).strip()
                                last_key = "description"
                                continue
                            # Property line
                            prop_match = self.PROPERTY_REGEX.match(line)
                            if prop_match:
                                key = prop_match.group(1).strip()
                                value = prop_match.group(2).strip()
                                if key.lower() != "description":
                                    current_element["properties"][key] = value
                                    last_key = key
                                continue
                            # Multi-line property or description continuation
                            if last_key:
                                if last_key == "description":
                                    current_element["description"] += " " + line
                                else:
                                    current_element["properties"][last_key] += " " + line
                                continue
                            # If no key, treat as generic property
                            if ':' not in line and current_element:
                                prop_key = f"Property_{len(current_element['properties'])+1}"
                                current_element["properties"][prop_key] = line
                    if current_element:
                        elements.append(current_element)
            logger.info(f"Successfully parsed PDF file: {pdf_path}")
            return elements
        except Exception as e:
            logger.error(f"Error parsing PDF file: {e}")
            raise

    # def _process_page_text(self, text: str, page_num: int) -> List[Dict]:
    #     elements = []
    #     lines = text.split('\n')
    #     current_element = None
    #     for line in lines:
    #         line = line.strip()
    #         if not line:
    #             continue
    #         if line.lower().startswith(('component:', 'screen:', 'section:')):
    #             if current_element:
    #                 elements.append(current_element)
    #             element_type, name = line.split(':', 1)
    #             current_element = {
    #                 'type': element_type.strip().upper(),
    #                 'name': name.strip(),
    #                 'description': '',
    #                 'properties': {},
    #                 'page': page_num
    #             }
    #         elif ':' in line and current_element:
    #             key, value = line.split(':', 1)
    #             key = key.strip().lower()
    #             value = value.strip()
    #             if key == 'description':
    #                 current_element['description'] = value
    #             else:
    #                 current_element['properties'][key] = value
    #     if current_element:
    #         elements.append(current_element)
    #     return elements