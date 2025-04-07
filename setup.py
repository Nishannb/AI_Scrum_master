from setuptools import setup, find_packages

setup(
    name="ai_scrum_master",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "uagents",
        "aiohttp",
        "pydantic",
    ],
    python_requires=">=3.8",
) 