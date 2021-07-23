import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ontology_processing",
    version="1.0.8",
    description="Climate Mind ontology processing code.",
    author="ClimateMind",
    author_email="hello@climatemind.org",
    url="https://github.com/ClimateMind/climatemind-ontology-processing",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    scripts=['ontology_processing/process_new_ontology_file.py'],
    python_requires=">=3.6",
    install_requires=[
        'Brotli',
        'click',
        'cycler',
        'dash',
        'dash-core-components',
        'dash-html-components',
        'dash-renderer',
        'dash-table',
        'decorator',
        'Flask',
        'Flask-Compress',
        'future',
        'itsdangerous',
        'Jinja2',
        'kiwisolver',
        'MarkupSafe',
        'matplotlib',
        'networkx',
        'numpy',
        'Owlready2',
        'pandas',
        'Pillow',
        'plotly',
        'pyparsing',
        'python-dateutil',
        'pytz',
        'retrying',
        'scipy',
        'six',
        'validators',
        'Werkzeug',
    ]
)
