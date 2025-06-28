from setuptools import setup, find_packages

setup(
    name="figma-to-jira",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-dotenv>=1.0.1",
        "requests>=2.31.0",
        "jira>=3.5.2",
        "openai>=1.7.2",
        "pydantic>=2.6.3",
        "loguru>=0.7.2",
        "langchain>=0.1.9",
        "python-jose>=3.3.0",
        "fastapi>=0.110.0",
        "uvicorn>=0.27.1",
        "python-multipart>=0.0.9",
        "PyYAML>=6.0.1",
        "httpx>=0.27.0",
        "aiohttp>=3.9.3",
        "typing-extensions>=4.9.0",
        "python-dateutil>=2.8.2",
    ],
    python_requires=">=3.8",
) 