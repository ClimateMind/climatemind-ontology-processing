import ontology_processing.process_new_ontology_file

onto_path = "Bx50aIKwEALYNmYl0CFzNp.owl"
output_folder_path = "."

ontology_processing.process_new_ontology_file.processOntology(
    onto_path, output_folder_path
)
