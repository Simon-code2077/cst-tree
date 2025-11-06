#!/bin/bash

# Setup script for cst-tree project
# This script clones the required tree-sitter-rust dependency

echo "Setting up cst-tree project..."

# Create vendor directory if it doesn't exist
mkdir -p vendor

# Clone tree-sitter-rust if not already present
if [ ! -d "vendor/tree-sitter-rust" ]; then
    echo "Cloning tree-sitter-rust..."
    git clone https://github.com/tree-sitter/tree-sitter-rust vendor/tree-sitter-rust
    cd vendor/tree-sitter-rust
    git checkout v0.20.4
    cd ../..
else
    echo "tree-sitter-rust already exists"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Build language library
echo "Building language library..."
python3 -c "
from splice_rust import ensure_language_built
ensure_language_built()
print('Language library built successfully!')
"

echo "Setup complete! You can now run:"
echo "  python3 splice_rust.py test.rs"