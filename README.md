# climatemind-ontology-processing

The ontology is stored as an OWL file (a type of RDF/XML file) which we convert to a NetworkX Graph using
Owlready2 (a Python library for processing an ontology). These files handle all of the
processing and visualization for the ontology.

## How to Process the Ontology

### Do this your first time

Install the Ontology from PyPi

```
python3 -m pip install ontology-processing
```

Ensure you have the correct version (1.0.8 at time of this writing) by checking

```
python3 -m pip list
```

If not, you can install a specific version like

```
python3 -m pip install ontology-processing==1.0.8
```

Now you're all set up and ready to roll! This should install the dependencies automatically.

### Do this every time
1. Download a fresh copy of the ontology from web protege. Make sure it's the RDF/XML format (check the downloaded item has .owl at the end of it!).
2. When using the code as a package, be sure to `import ontology_processing.process_new_ontology_file`
3. Use the function `ontology_processing.process_new_ontology_file.processOntology(onto_path, output_folder_path)` where onto path is the path of the .owl ontology file and output_folder_path is the path to a folder for the output files to go into.
4. Check your output in your output folder. You should have a pickle file, a json file and a csv

You now have a fresh copy of the NetworkX graph to use for the climatemind-backend Flask app!



### Alternatively, if prefer not to use the code as a package installed using pip, then:
1. Download a fresh copy of the ontology from web protege. Make sure it's the RDF/XML format (check the downloaded item has .owl at the end of it!).
2. Clone the climatemind-ontology-processing directory to your local machine
3. Use the command line/terminal to navigate to the climatemind-ontology-processing directory and run the following command
```
pip install -e ./
```

This will install a local editable pip package which you can use to test code updates or process the ontology with the locally
downloaded repo.

4. Use the function `ontology_processing.process_new_ontology_file.processOntology(onto_path, output_folder_path)` where onto path is the path of the .owl ontology file and output_folder_path is the path to a folder for the output files to go into.
5. Check your output in your output folder. You should have a pickle file, a json file and a csv
You now have a fresh copy of the NetworkX graph to use for the climatemind-backend Flask app!