# From an input OWL file, process it to make files needed for Climate Mind app production and to run helper scripts like visualize.py. Be sure to run from the "backend" folder (not from "knowledge_graph")

import os
import argparse

import ontology_processing.graph_creation.make_network as make_network
import ontology_processing.graph_creation.make_graph as make_graph


def processOntology(onto_path, output_folder_path):
    """
    Main function that builds files from OWL file starter file. Saved these files to the knowledge_graph repo (note these added files are ignored by git so they don't end up in github later if they are present during a git push). This function should be run from backend repo folder.

    input: args = args from the argument parser for the function (refOntologyPath)
    output: saves all ontology-related files needed and used by scripts for the Climate Mind app and tools to knowledge_graph folder.

    example: python3 process_new_ontology_file.py "./climate_mind_ontology20200721.owl"
    """
    # build output path
    csv_path = os.path.join(output_folder_path, "output.csv")

    # get the network edges from the OWL ontology object
    make_network.outputEdges(onto_path=onto_path, output_path=csv_path, source=None)

    # from the network edges, make a networkx graph and save as a pickle file
    make_graph.make_graph(onto_path, csv_path, output_folder_path)


def main(args):
    """
    Main function that builds files from OWL file starter file. Saved these files to the knowledge_graph repo (note these added files are ignored by git so they don't end up in github later if they are present during a git push). This function should be run from backend repo folder.

    input: args = args from the argument parser for the function (refOntologyPath)
    output: saves all ontology-related files needed and used by scripts for the Climate Mind app and tools to knowledge_graph folder.

    example: python3 process_new_ontology_file.py "./climate_mind_ontology20200721.owl"
    """
    # set arguments
    output_folder_path = args.output_folder

    onto_path = args.OWL_file

    # process the OWL ontology file
    processOntology(onto_path=onto_path, output_folder_path=output_folder_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='From a new ontology OWL file, process it, and files needed by Climate Mind app and associated scripts like visualize.py. Be sure to run from the "backend" folder (not from "knowledge_graph")'
    )
    parser.add_argument("OWL_file", type=str, help="path to OWL file")
    parser.add_argument("output_folder", type=str, help="Path to output folder")

    args = parser.parse_args()
    main(args)
