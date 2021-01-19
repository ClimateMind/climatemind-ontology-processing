# climatemind-ontology-processing

The ontology is stored as an RDF/XML file which we convert to a NetworkX Graph using
Owlready2 (a Python library for processing an ontology). These files handle all of the
processing and visualization for the ontology.

## How to Process the Ontology

### Do this your first time

1. Clone the climatemind-ontology-processing directory to your local machine
2. Use the command line/terminal to navigate to the climatemind-ontology-processing directory
3. Create a virtual env
```
python3 -m venv venv
source venv/bin/activate
```
4. Install the dependencies
```
pip install -r requirements.txt
```

Now you're all set up and ready to roll!

### Do this every time
1. Download a fresh copy of the ontology from web protege. Make sure it's the RDF/XML format.
2. Rename this file to climate\_mind\_ontology (make sure to remove the file extension)
3. Copy the file into the PUT\_NEW\_OWL\_FILE\_IN\_HERE
4. Open your virtual env in the command line/terminal (you should be in the climatemind-ontology-processing directory)
```
source venv/bin/activate
```
5. Run one of the two main scripts 
```
python3 process_new_ontology_file.py
# or
python3 process_new_ontology_and_visualize.py
```

6. Check your output in the Output folder. You should have a pickle file, a json file and a csv

You now have a fresh copy of the NetworkX graph to use for the backend app!







