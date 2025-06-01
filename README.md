# pa-permission-dependency-graph
Creates a visual dependency graph showing how different permissions rely on each other. Highlights circular dependencies or critical single points of failure in permission structures. Uses graphviz for visualization. - Focused on Tools for analyzing and assessing file system permissions

## Install
`git clone https://github.com/ShadowStrikeHQ/pa-permission-dependency-graph`

## Usage
`./pa-permission-dependency-graph [params]`

## Parameters
- `-h`: Show help message and exit
- `-d`: The directory to analyze permissions from.
- `-o`: No description provided
- `-v`: Enable verbose logging.
- `-f`: No description provided
- `--detect-circular`: Detect and highlight circular permission dependencies.

## License
Copyright (c) ShadowStrikeHQ
