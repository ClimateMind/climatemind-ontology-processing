from setuptools import setup, find_packages

setup(
    name="climatemind-ontology-processing",
    version="1.0.0",
    description="Climate Mind ontology processing code.",
    author="ClimateMind",
    url="https://github.com/ClimateMind/climatemind-ontology-processing",
    packages=find_packages(
        exclude=["docs", "tests", ".gitignore", "README.rst", "DESCRIPTION.rst"]
    ),
)
