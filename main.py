#!/usr/bin/env python3

import argparse
import logging
import os
import sys
from collections import defaultdict
from typing import Dict, List, Set

try:
    import graphviz
    from rich.console import Console
    from rich.table import Column, Table
except ImportError as e:
    print(f"Error: Missing required libraries: {e}. Please install them using 'pip install graphviz rich'")
    sys.exit(1)


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Creates a visual dependency graph showing how different permissions rely on each other.",
                                     epilog="Example Usage: python main.py -d /path/to/permissions -o output")

    parser.add_argument("-d", "--directory", dest="directory", required=True,
                        help="The directory to analyze permissions from.")
    parser.add_argument("-o", "--output", dest="output_file", required=True,
                        help="The output name for the graph, without a file extension (e.g., output). The format extension is appended when the graph is rendered, so -o output with format png writes output.png.")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose",
                        help="Enable verbose logging.")
    parser.add_argument("-f", "--format", dest="format", default="png",
                        help="The output format for the graph (e.g., png, pdf, svg). Defaults to png.")
    parser.add_argument("--detect-circular", action="store_true", dest="detect_circular",
                        help="Detect and highlight circular permission dependencies.")
    return parser.parse_args()


def get_file_permissions(directory: str, verbose: bool = False) -> Dict[str, Set[str]]:
    """
    Retrieves the permissions for files within a directory.
    This is a simplified example and might need adjustment based on the actual permission retrieval mechanism.

    Args:
        directory: The directory to analyze.

    Returns:
        A dictionary where the key is the file path and the value is a set of permissions.
    """
    permissions: Dict[str, Set[str]] = {}

    if not os.path.isdir(directory):
        logging.error(f"Error: '{directory}' is not a valid directory.")
        raise ValueError(f"'{directory}' is not a valid directory.")

    # Directories never enter the map at all. An empty directory, and
    # the directory entries themselves, leave no trace in the graph, so
    # the picture is files only even though the walk passes every folder.
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)

            try:
                # This is a very basic simulation; replace with actual permission retrieval
                # In a real implementation, this would involve checking ACLs, file modes, etc.
                stat_info = os.stat(file_path)
                mode = stat_info.st_mode

                # Example permissions (replace with more accurate representation)
                file_permissions: Set[str] = set()
                if mode & 0o400: #read by owner
                    file_permissions.add("read_owner")
                if mode & 0o200: #write by owner
                    file_permissions.add("write_owner")
                if mode & 0o100: #execute by owner
                    file_permissions.add("execute_owner")

                if mode & 0o040: #read by group
                    file_permissions.add("read_group")
                if mode & 0o020: #write by group
                    file_permissions.add("write_group")
                if mode & 0o010: #execute by group
                    file_permissions.add("execute_group")

                if mode & 0o004: #read by others
                    file_permissions.add("read_others")
                if mode & 0o002: #write by others
                    file_permissions.add("write_others")
                if mode & 0o001: #execute by others
                    file_permissions.add("execute_others")

                permissions[file_path] = file_permissions

                if verbose:
                    logging.info(f"Permissions for '{file_path}': {file_permissions}")

            except OSError as e:
                logging.error(f"Error getting permissions for '{file_path}': {e}")

    return permissions


def analyze_permission_dependencies(permissions: Dict[str, Set[str]]) -> Dict[str, List[str]]:
    """
    Analyzes permission dependencies based on the retrieved file permissions.

    Args:
        permissions: A dictionary of file paths and their corresponding permissions.

    Returns:
        A dictionary representing permission dependencies, where the key is a permission
        and the value is a list of permissions it depends on.  This is a simplified placeholder,
        a more nuanced implementation would examine the relationships between permissions.
    """
    # The graph is built per resource: a node per file, plus one node
    # per permission of that file, named "<file>: <permission>". The
    # stated rules are applied to that file's own permissions: write
    # depends on read, and execute depends on read and on write, in
    # each of the owner, group, and others families. Edges are
    # deduplicated.
    raw: Dict[str, Set[str]] = defaultdict(set)

    for file_path, perms in permissions.items():
        for perm in perms:
            raw[file_path].add(f"{file_path}: {perm}")
        for family in ("owner", "group", "others"):
            write_node = f"{file_path}: write_{family}"
            read_node = f"{file_path}: read_{family}"
            execute_node = f"{file_path}: execute_{family}"
            if f"write_{family}" in perms:
                raw[write_node].add(read_node)
            # Both edges are added whenever execute exists, even when
            # this file has no write permission in that family. The
            # render step then draws a write node the file never had,
            # as a dependency of its execute node.
            if f"execute_{family}" in perms:
                raw[execute_node].add(read_node)
                raw[execute_node].add(write_node)

    dependencies: Dict[str, List[str]] = {node: sorted(deps) for node, deps in raw.items()}
    return dependencies

def detect_circular_dependencies(dependencies: Dict[str, List[str]]) -> List[List[str]]:
    """
    Detects circular dependencies in the permission structure.

    Args:
        dependencies: A dictionary representing permission dependencies.

    Returns:
        A list of circular dependency paths.
    """

    # Visited and stack are built over every node named on either
    # side of the dependency map, so a node that appears only as a
    # dependency value is still tracked and cannot raise a KeyError.
    nodes = set(dependencies.keys())
    for deps in dependencies.values():
        nodes.update(deps)
    visited = {node: False for node in nodes}
    stack = {node: False for node in nodes}
    cycles: List[List[str]] = []

    def find_cycles(node, graph, path):
        visited[node] = True
        stack[node] = True
        path.append(node)

        for neighbor in graph.get(node, []):
            if not visited[neighbor]:
                find_cycles(neighbor, graph, path)
            elif stack[neighbor]:
                start = path.index(neighbor)
                cycles.append(path[start:] + [neighbor])

        path.pop()
        stack[node] = False

    for node in sorted(nodes):
        if not visited[node]:
            find_cycles(node, dependencies, [])

    return cycles


def create_dependency_graph(dependencies: Dict[str, List[str]], output_file: str, graph_format: str = "png", highlight_circular: bool = False):
    """
    Creates a visual dependency graph using graphviz.

    Args:
        dependencies: A dictionary representing permission dependencies.
        output_file: The output file for the graph.
        graph_format: The desired output format (e.g., png, pdf).
    """
    dot = graphviz.Digraph(comment='Permission Dependency Graph')

    for permission, deps in dependencies.items():
        dot.node(permission, permission)  # Add nodes for all permissions
        for dep in deps:
            dot.node(dep, dep) #Add all dependencies as nodes.
            dot.edge(permission, dep)

    if highlight_circular:
        circular_dependencies = detect_circular_dependencies(dependencies)
        if circular_dependencies:
            print("[!] Circular dependencies detected:")
            for cycle in circular_dependencies:
                print(" -> ".join(cycle))
        # The red edge drawing sits in this no cycles branch, where the
        # loop over circular_dependencies runs over an empty list. When
        # cycles are found above I print them and draw nothing, so the
        # highlight flag never actually colours an edge.
        else:
            print("No circular dependencies detected.")

            for cycle in circular_dependencies:
                for i in range(len(cycle) - 1):
                    dot.edge(cycle[i], cycle[i+1], color="red", penwidth="2.0")
                # Highlight closing edge in cycle
                dot.edge(cycle[-1], cycle[0], color="red", penwidth="2.0") # close the cycle

    try:
        rendered = dot.render(output_file, format=graph_format, cleanup=True)  # Create the graph image
        logging.info(f"Graph created successfully: {rendered}")
        return rendered

    except graphviz.backend.ExecutableNotFound as e:
        logging.error(f"Error: Graphviz executable not found.  Please ensure Graphviz is installed and in your PATH.  Details: {e}")
        print("Error: Graphviz executable not found. Please ensure Graphviz is installed and in your PATH.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error generating graph: {e}")
        print(f"Error generating graph: {e}")
        sys.exit(1)



def main():
    """
    Main function to orchestrate the permission dependency graph generation.
    """
    args = setup_argparse()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        directory = args.directory
        output_file = args.output_file
        output_format = args.format

        if not os.path.isdir(directory):
            raise ValueError(f"The specified directory '{directory}' does not exist.")

        permissions = get_file_permissions(directory, verbose=args.verbose)
        if not permissions:
            print(f"Error: No files found in directory '{directory}'. No graph was generated.")
            logging.error(f"No files found in directory '{directory}'.")
            sys.exit(1)
        dependencies = analyze_permission_dependencies(permissions)
        rendered = create_dependency_graph(dependencies, output_file, output_format, args.detect_circular)

        print(f"Permission dependency graph generated successfully at {rendered}")

    except ValueError as e:
        logging.error(e)
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.exception("An unexpected error occurred:")  # Log the full exception
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)



if __name__ == "__main__":
    # Example Usage:
    # python main.py -d /path/to/your/directory -o output
    # python main.py -d /path/to/your/directory -o output -f pdf
    # python main.py -d /path/to/your/directory -o output -v # verbose
    # python main.py -d /path/to/your/directory -o output --detect-circular
    # Create a sample directory structure for testing
    # os.makedirs("sample_dir/subdir", exist_ok=True)
    # open("sample_dir/file1.txt", "a").close()
    # open("sample_dir/subdir/file2.txt", "a").close()

    main()