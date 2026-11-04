# pa-permission-dependency-graph
Creates a visual dependency graph of the files in a directory, showing how the permissions of each file rely on each other. The graph is built per resource: there is a node per file, and edges from the stated rules applied to that file's own permissions (write depends on read, and execute depends on read and on write, in each of the owner, group, and others families), deduplicated. With --detect-circular, circular dependencies in that graph are reported and highlighted. Uses graphviz for visualization. An empty directory exits 1 with a no files found line and writes no graph. - Focused on Tools for analyzing and assessing file system permissions

## Install
`git clone https://github.com/ShadowGuard-AI/pa-permission-dependency-graph`

Prerequisite: the Graphviz system executable (dot) must be installed and in your PATH, in addition to the Python packages in requirements.txt.

## Usage
`python3 main.py -d /path/to/directory -o output [options]`

The output name is given without a file extension: rendering appends the format extension, so the example above writes output.png, not output.png.png.

## Parameters
- `-h`: Show help message and exit
- `-d`, `--directory`: (required) The directory to analyze permissions from.
- `-o`, `--output`: (required) The output name for the graph, without a file extension (e.g., output). The format extension is appended when the graph is rendered, so -o output with format png writes output.png.
- `-v`, `--verbose`: Enable verbose logging.
- `-f`, `--format`: The output format for the graph (e.g., png, pdf, svg). Defaults to png.
- `--detect-circular`: Detect and highlight circular permission dependencies.

## License
See LICENSE.
