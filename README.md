# CST-Tree: Rust Code Mutation ToolRust tree-sitter parsing helper



A Python-based tool for performing semantic-aware code mutations on Rust source code using tree-sitter. This project implements tree-splicer-like functionality for educational and research purposes.This small project demonstrates using tree-sitter from Python to parse Rust source files.



## FeaturesLocation



- **Semantic-aware mutations**: Prioritizes meaningful code structure changes over trivial identifier replacements    /home/hangye/rust

- **Tree-sitter integration**: Uses tree-sitter for accurate Rust parsing and AST manipulation  

- **Priority-based replacement**: Intelligent node selection favoring blocks, expressions, and statementsFiles

- **Safety mechanisms**: Protects critical functions and maintains code validity

- **Recursive algorithm**: Top-down replacement strategy with re-parsing after each mutation- `parse_rust.py` - main script: builds/loads tree-sitter Rust language and parses a Rust file (default `test.rs`).

- `requirements.txt` - Python runtime dependency (`tree_sitter`).

## Installation- `vendor/` - (created by the script) will contain the cloned `tree-sitter-rust` grammar if needed.

- `build/` - (created by the script) will contain the built `my-languages.so` shared library.

1. Clone this repository:

```bashQuick setup (Linux)

git clone <repository-url>

cd cst-tree1. Install system build deps (one-liner for Debian/Ubuntu-like systems):

```

```bash

2. Run the setup script:sudo apt update

```bashsudo apt install -y build-essential git python3-dev python3-venv

./setup.sh```

```

2. Create and activate a venv (recommended):

This will:

- Clone the required tree-sitter-rust grammar```bash

- Install Python dependenciescd /home/hangye/rust/cst-tree

- Build the language librarypython3 -m venv .venv

source .venv/bin/activate

## Usagepip install -r requirements.txt

```

Basic usage:

```bash3. Prepare a Rust source file named `test.rs` in this directory (or point the script to another path).

python3 splice_rust.py input.rs

```4. Run the parser:



With options:```bash

```bashpython3 parse_rust.py test.rs

python3 splice_rust.py input.rs --output output.rs --mutations 10 --seed 42```

```

What the script does

### Command Line Options

- If `build/my-languages.so` does not exist, the script clones `https://github.com/tree-sitter/tree-sitter-rust` into `vendor/tree-sitter-rust` and calls `Language.build_library` to produce `build/my-languages.so`.

- `input`: Input Rust file to mutate- It then parses the given Rust file and prints the CST (s-expression) and a list of top-level functions discovered via a simple query.

- `--output, -o`: Output file path (prints to stdout if not specified)

- `--mutations, -m`: Number of mutations to perform (default: 16)Troubleshooting

- `--seed, -s`: Random seed for reproducible results (default: 42)

- If the build fails, ensure you have a working C compiler and Python dev headers.

## Examples- If you prefer not to build, you can pre-build the library on another machine and copy `build/my-languages.so` into this project's `build/` folder.



The project includes several test files:Next steps / Enhancements



- `test.rs`: Simple function with basic operations- Add queries to extract more Rust constructs (macros, unsafe blocks, trait declarations).

- `complex_test.rs`: More complex code with multiple functions and control flow- Integrate with rustc/rust-analyzer to obtain semantic/type information for semantic-aware mutations.

- `expr_test.rs`: Expression-focused test cases- Add a CLI flag to output parsed tree to JSON or to pretty-print AST nodes.

- `small_test.rs`: Minimal test case

Try them out:
```bash
python3 splice_rust.py test.rs --mutations 5
python3 splice_rust.py complex_test.rs --output mutated.rs
```

## How It Works

### Priority System

The tool uses a sophisticated priority system to ensure meaningful mutations:

1. **High Priority** (1-6): Structural nodes
   - `block`: Code blocks - most impactful changes
   - `binary_expression`: Arithmetic/logical expressions  
   - `call_expression`: Function calls
   - `let_declaration`: Variable declarations

2. **Medium Priority** (10-13): Data nodes
   - `string_literal`, `integer_literal`: Literal values
   - `parameters`, `arguments`: Function parameters

3. **Low Priority** (20+): Identifiers
   - `identifier`: Variable names - least impactful

### Algorithm Overview

1. **Parse**: Use tree-sitter to parse Rust source into AST
2. **Collect**: Gather all possible replacement candidates by node type
3. **Prioritize**: Sort candidates by structural importance and depth
4. **Replace**: Perform recursive replacement starting from root
5. **Re-parse**: Rebuild AST after each mutation to maintain accuracy
6. **Validate**: Ensure output is syntactically correct

### Safety Features

- **Function Protection**: Prevents replacement of `main` and other critical functions
- **Keyword Protection**: Avoids replacing Rust keywords and standard library functions  
- **Duplicate Prevention**: Prevents creating duplicate function names
- **Syntax Validation**: Verifies output compiles correctly

## Project Structure

```
cst-tree/
├── splice_rust.py       # Main mutation tool (complete implementation)
├── setup.sh            # Installation script
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── .gitignore         # Git ignore rules
├── test.rs            # Test files
├── complex_test.rs
├── expr_test.rs
├── small_test.rs
├── build/             # Compiled language libraries (auto-generated)
└── vendor/            # External dependencies (auto-downloaded)
```

## Development

The tool is designed for educational purposes to understand:
- Tree-sitter parsing and AST manipulation
- Semantic-aware code mutation strategies
- Priority-based node selection algorithms
- Safe code transformation techniques

## Requirements

- Python 3.7+
- Git (for cloning dependencies)
- GCC/Clang (for building tree-sitter libraries)

See `requirements.txt` for Python package dependencies.

## License

This project is for educational and research purposes. Please check the licenses of tree-sitter and tree-sitter-rust for their respective terms.