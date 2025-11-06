#!/usr/bin/env python3
"""
splice_rust.py

A utility that demonstrates tree-sitter node replacement/splicing for Rust code.
Based on the tree-splicer approach but simplified for learning purposes.

Usage: python3 splice_rust.py input.rs [--output output.rs] [--mutations N]
"""

import argparse
import random
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

try:
    from tree_sitter import Language, Parser, Query, Node
except Exception as e:
    print("tree_sitter Python package not found. Please run: pip install -r requirements.txt", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parent
BUILD_DIR = ROOT / "build"
VENDOR_DIR = ROOT / "vendor"
RUST_SO = BUILD_DIR / "my-languages.so"
TREE_SITTER_RUST = VENDOR_DIR / "tree-sitter-rust"


def ensure_language_built():
    """Ensure Rust language library exists"""
    if not RUST_SO.exists():
        print("Language library not found. Please run parse_rust.py first to build it.")
        sys.exit(1)


class NodeReplacer:
    """Node replacer, similar to tree-splicer functionality"""
    
    def __init__(self, language: Language, seed: int = 42):
        self.language = language
        self.parser = Parser()
        self.parser.set_language(language)
        self.rng = random.Random(seed)
        self.node_pools: Dict[str, List[bytes]] = defaultdict(list)
        self.variable_tracker: Dict[str, int] = {}  # Track variable declaration positions
        self.function_names_used: set = set()  # Track used function names
        self.priority_order = [  # Node replacement priority order
            'let_declaration',
            'identifier', 
            'binary_expression',
            'call_expression',
            'block',
            'function_item'
        ]
    
    def collect_nodes(self, source_bytes: bytes, tree) -> None:
        """Collect all node types and their corresponding code snippets"""
        self._collect_recursive(tree.root_node, source_bytes)
    
    def _collect_recursive(self, node: Node, source_bytes: bytes) -> None:
        """Recursively collect nodes"""
        node_kind = node.type
        node_text = source_bytes[node.start_byte:node.end_byte]
        
        # Only collect meaningful nodes (not too big or too small)
        if 5 <= len(node_text) <= 200 and not node_kind.startswith('_'):
            self.node_pools[node_kind].append(node_text)
        
        # Recursively process child nodes
        for i in range(node.child_count):
            child = node.child(i)
            if child:
                self._collect_recursive(child, source_bytes)
    
    def print_node_pools(self) -> None:
        """Print collected node pools"""
        print("=== Collected Node Pools ===")
        for kind, texts in self.node_pools.items():
            print(f"{kind}: {len(texts)} candidates")
            for i, text in enumerate(texts[:]):  
                preview = text.decode('utf-8', errors='replace').replace('\n', '\\n')
                if len(preview) > 50:
                    preview = preview[:47] + "..."
                print(f"  [{i}] {preview}")
            print()
    
    def find_replaceable_nodes_ordered(self, tree) -> List[Node]:
        """Find replaceable nodes from root node in priority order"""
        all_candidates = []
        self._find_replaceable_recursive_ordered(tree.root_node, all_candidates, depth=0)
        
        # Sort by priority and depth
        ordered_candidates = self._sort_by_priority_and_position(all_candidates)
        
        # Build variable tracking table
        self._build_variable_tracker(ordered_candidates)
        
        return ordered_candidates
    
    def _find_replaceable_recursive_ordered(self, node: Node, candidates: List[Tuple[Node, int]], depth: int) -> None:
        """Recursively find replaceable nodes, record depth information"""
        # Only consider node types with replacement candidates
        if node.type in self.node_pools and len(self.node_pools[node.type]) > 1:
            candidates.append((node, depth))
        
        # Recursively process child nodes
        for i in range(node.child_count):
            child = node.child(i)
            if child:
                self._find_replaceable_recursive_ordered(child, candidates, depth + 1)
    
    def _sort_by_priority_and_position(self, candidates: List[Tuple[Node, int]]) -> List[Node]:
        """Sort nodes by position, but ensure let_declaration has priority within same scope"""
        def priority_key(item):
            node, depth = item
            node_type = node.type
            
            # Sort primarily by position, but let_declaration has priority within same position range
            base_priority = node.start_byte
            
            # let_declaration gets priority within same small range
            if node_type == 'let_declaration':
                base_priority -= 0.1  # Slightly ahead
            
            return base_priority
        
        sorted_candidates = sorted(candidates, key=priority_key)
        return [node for node, depth in sorted_candidates]
    
    def _build_variable_tracker(self, ordered_nodes: List[Node]) -> None:
        """Build variable tracking table, ensure let_declaration appears before variables of same name"""
        self.variable_tracker.clear()
        
        for i, node in enumerate(ordered_nodes):
            if node.type == 'let_declaration':
                # Extract variable name (simplified processing)
                var_name = self._extract_variable_name_from_let(node)
                if var_name:
                    self.variable_tracker[var_name] = i
                    print(f"Tracking variable declaration: {var_name} at position {i}")
    
    def _extract_variable_name_from_let(self, let_node: Node) -> Optional[str]:
        """Extract variable name from let_declaration node"""
        # Traverse child nodes to find identifier
        for i in range(let_node.child_count):
            child = let_node.child(i)
            if child and child.type == 'identifier':
                return child.text.decode('utf-8', errors='replace')
        return None
    
    def _can_replace_identifier(self, node: Node, position: int) -> bool:
        """Check if identifier node can be replaced"""
        if node.type != 'identifier':
            return True
        
        var_name = node.text.decode('utf-8', errors='replace')
        
        # If this variable has declaration, check if it's after the declaration
        if var_name in self.variable_tracker:
            declaration_pos = self.variable_tracker[var_name]
            if position <= declaration_pos:
                print(f"Skipping variable {var_name}: declaration position {declaration_pos}, current position {position}")
                return False
        
        return True
    
    def perform_replacement_recursive(self, source_bytes: bytes, tree, num_mutations: int = 1) -> Optional[bytes]:
        """Start recursive replacement from root - child nodes change after replacing a node"""
        if num_mutations <= 0:
            return None
            
        print(f"Starting recursive replacement, max {num_mutations} mutations")
        
        # Collect function names in current code
        self._collect_function_names(tree.root_node, source_bytes)
        print(f"🔍 Found function names: {self.function_names_used}")
        
        # Start recursive search and replacement from root
        result_bytes = bytearray(source_bytes)
        mutations_count = [0]  # Use list to modify in recursion
        
        # Re-parse to get latest tree structure
        new_tree = self.parser.parse(bytes(result_bytes))
        
        success = self._recursive_replace_from_node(
            new_tree.root_node, 
            result_bytes, 
            mutations_count, 
            num_mutations,
            bytes(result_bytes)
        )
        
        if mutations_count[0] == 0:
            print("No replacements performed")
            return None
            
        print(f"Total {mutations_count[0]} replacements performed")
        return bytes(result_bytes)
    
    def _collect_function_names(self, node: Node, source_bytes: bytes) -> None:
        """Collect all function names in the code"""
        self.function_names_used.clear()
        
        if node.type == 'function_item':
            # Find function name (usually the second child node)
            for i in range(node.child_count):
                child = node.child(i)
                if child and child.type == 'identifier':
                    func_name = source_bytes[child.start_byte:child.end_byte].decode('utf-8', errors='replace')
                    self.function_names_used.add(func_name)
                    break
        
        # Recursively process child nodes
        for i in range(node.child_count):
            child = node.child(i)
            if child:
                self._collect_function_names(child, source_bytes)
    
    def _recursive_replace_from_node(self, node: Node, result_bytes: bytearray, 
                                   mutations_count: List[int], max_mutations: int,
                                   current_source: bytes, depth: int = 0) -> bool:
        """Recursively replace from specified node - prioritize meaningful nodes"""
        if mutations_count[0] >= max_mutations:
            return True  # Reached max replacements
        
        indent = "  " * depth
        print(f"{indent}🔍 Exploring node: {node.type} [{node.start_byte}:{node.end_byte}] (depth {depth})")
        
        # First collect all replaceable nodes in current node and its children
        replaceable_candidates = []
        self._collect_replaceable_candidates(node, replaceable_candidates, depth)
        
        # Sort candidate nodes by priority
        prioritized_candidates = self._prioritize_candidates(replaceable_candidates)
        
        # Try to replace the highest priority node
        for candidate_node, candidate_depth in prioritized_candidates:
            if mutations_count[0] >= max_mutations:
                break
                
            print(f"{indent}✅ Selected replacement node: {candidate_node.type} (depth {candidate_depth})")
            
            if self._try_replace_current_node(candidate_node, result_bytes, mutations_count, current_source, candidate_depth):
                print(f"{indent}🔄 Replaced {candidate_node.type}, re-parsing entire file")
                
                # Re-parse entire file after replacement
                new_source = bytes(result_bytes)
                new_tree = self.parser.parse(new_source)
                
                # Start over from root node
                return self._recursive_replace_from_node(
                    new_tree.root_node, 
                    result_bytes, 
                    mutations_count, 
                    max_mutations,
                    new_source,
                    depth=0  # Start over, reset depth to 0
                )
        
        return False  # No replacements occurred
    
    def _collect_replaceable_candidates(self, node: Node, candidates: List, depth: int) -> None:
        """Collect all replaceable candidate nodes in current node and its subtree"""
        # Check current node
        if self._can_replace_node(node):
            candidates.append((node, depth))
        
        # Recursively collect child nodes
        for i in range(node.child_count):
            child = node.child(i)
            if child:
                self._collect_replaceable_candidates(child, candidates, depth + 1)
    
    def _prioritize_candidates(self, candidates: List) -> List:
        """Sort candidate nodes by priority"""
        def get_priority(item):
            node, depth = item
            node_type = node.type
            
            # Define priority weights (lower number = higher priority)
            priority_weights = {
                'block': 1,              # Highest priority
                'binary_expression': 2,
                'call_expression': 3,
                'let_declaration': 4,
                'expression_statement': 5,
                'macro_invocation': 6,
                'string_literal': 10,    # Medium priority
                'integer_literal': 11,
                'parameters': 12,
                'arguments': 13,
                'identifier': 20,        # Lowest priority
                'type_identifier': 21,
            }
            
            weight = priority_weights.get(node_type, 15)  # Default medium priority
            
            # For same priority, prefer shallower nodes
            return (weight, depth)
        
        return sorted(candidates, key=get_priority)
    
    def _can_replace_node(self, node: Node) -> bool:
        """Check if node can be replaced - prioritize meaningful large-grain nodes"""
        if node.type not in self.node_pools:
            return False
        if len(self.node_pools[node.type]) <= 1:
            return False
        if node.type.startswith('_'):
            return False
            
        # Skip top-level declarations but don't block deep exploration
        skip_but_explore_types = {
            'function_item',    # Skip function declaration itself, but explore internals
            'struct_item',      # Skip struct declaration, but explore internals 
            'impl_item',        # Skip impl block, but explore internals
            'mod_item',         # Skip module declaration
            'use_declaration',  # Skip use statement
            'source_file',      # Skip root node
        }
        
        if node.type in skip_but_explore_types:
            return False  # Don't replace these nodes themselves, but continue exploring child nodes
        
        # Define node priority: prioritize large-grain, meaningful nodes
        high_priority_types = {
            'block',               # Code block - most meaningful replacement
            'binary_expression',   # Binary expression 
            'call_expression',     # Function call
            'let_declaration',     # Let statement
            'expression_statement', # Expression statement
            'macro_invocation',    # Macro invocation
        }
        
        medium_priority_types = {
            'string_literal',      # String literal
            'integer_literal',     # Integer literal
            'parameters',          # Parameter list
            'arguments',           # Arguments
        }
        
        low_priority_types = {
            'identifier',          # Identifier - consider last
            'type_identifier',     # Type identifier
        }
        
        # Prioritize high priority nodes
        if node.type in high_priority_types:
            return True
        elif node.type in medium_priority_types:
            return True  
        elif node.type in low_priority_types:
            return True
        else:
            return True  # Other types also allowed, but lower priority
    
    def _try_replace_current_node(self, node: Node, result_bytes: bytearray, 
                                 mutations_count: List[int], current_source: bytes, depth: int) -> bool:
        """Try to replace current node"""
        node_type = node.type
        candidates = self.node_pools[node_type]
        
        if len(candidates) <= 1:
            return False
        
        # Get original text
        original_text = current_source[node.start_byte:node.end_byte]
        
        # Choose a different candidate
        replacement_candidates = [c for c in candidates if c != original_text]
        if not replacement_candidates:
            return False
        
        replacement = self.rng.choice(replacement_candidates)
        
        # Check variable declaration order and function name safety
        if node_type == 'identifier':
            var_name = original_text.decode('utf-8', errors='replace')
            
            # Basic safety check
            if not self._is_safe_identifier_replacement(var_name, node.start_byte):
                print(f"{'  ' * depth}⚠️  Skipping unsafe identifier replacement: {var_name}")
                return False
            
            # Check if it's a function name (simple heuristic: check if parent node is function_item)
            if self._is_function_name(node, current_source):
                replacement_name = replacement.decode('utf-8', errors='replace')
                if not self._is_safe_function_name_replacement(var_name, replacement_name):
                    print(f"{'  ' * depth}⚠️  Skipping unsafe function name replacement: {var_name} → {replacement_name}")
                    return False
        
        indent = "  " * depth
        print(f"{indent}🎯 [Replacement #{mutations_count[0] + 1}] {node_type} (depth {depth})")
        print(f"{indent}   Position: {node.start_byte}-{node.end_byte}")
        print(f"{indent}   Original: '{original_text.decode('utf-8', errors='replace').replace('\n', '\\n')}'")
        print(f"{indent}   Replace with: '{replacement.decode('utf-8', errors='replace').replace('\n', '\\n')}'")
        
        # Perform replacement
        result_bytes[node.start_byte:node.end_byte] = replacement
        mutations_count[0] += 1
        
        return True
    
    def _is_safe_identifier_replacement(self, var_name: str, position: int) -> bool:
        """Check identifier replacement safety"""
        # Protect critical function names
        critical_functions = {'main', 'test'}
        if var_name in critical_functions:
            print(f"🛡️  Protecting critical function name: {var_name}")
            return False
        
        # Protect standard library function names
        stdlib_functions = {'println', 'print', 'panic', 'vec', 'format'}
        if var_name in stdlib_functions:
            print(f"🛡️  Protecting standard library function name: {var_name}")
            return False
            
        return True
    
    def _is_safe_function_name_replacement(self, current_name: str, new_name: str) -> bool:
        """Check if function name replacement is safe"""
        # Protect main function
        if current_name == 'main':
            print(f"🛡️  Cannot replace main function name")
            return False
        
        # Prevent function name duplication
        if new_name in self.function_names_used and new_name != current_name:
            print(f"🛡️  Avoiding duplicate function name: {new_name}")
            return False
        
        # Protect critical function names
        critical_functions = {'main', 'test'}
        if new_name in critical_functions and current_name != new_name:
            print(f"🛡️  Cannot use critical function name: {new_name}")
            return False
            
        return True
    
    def _is_function_name(self, node: Node, source_bytes: bytes) -> bool:
        """Check if node is a function name"""
        # Simple heuristic: check parent node and position in parent
        parent = node.parent
        if parent and parent.type == 'function_item':
            # In function_item, function name is usually the second child (first is 'fn' keyword)
            for i in range(parent.child_count):
                child = parent.child(i)
                if child and child.id == node.id:
                    return i == 1  # Second child (index 1) is usually the function name
        return False


def parse_and_replace(input_path: Path, output_path: Optional[Path] = None, 
                     num_mutations: int = 16, seed: int = 42) -> None:
    """Parse and replace code"""
    ensure_language_built()
    
    # Load language
    RUST = Language(str(RUST_SO), "rust")
    
    # Read input file
    source_bytes = input_path.read_bytes()
    
    # Parse
    parser = Parser()
    parser.set_language(RUST)
    tree = parser.parse(source_bytes)
    
    print(f"Parsing file: {input_path}")
    print(f"File size: {len(source_bytes)} bytes")
    print()
    
    # Create replacer and collect nodes
    replacer = NodeReplacer(RUST, seed)
    replacer.collect_nodes(source_bytes, tree)
    replacer.print_node_pools()
    
    # Perform replacement
    result = replacer.perform_replacement_recursive(source_bytes, tree, num_mutations)
    
    if result is None:
        print("No replacement result generated")
        return
    
    # Verify if replaced code can be parsed
    try:
        new_tree = parser.parse(result)
        if new_tree.root_node.has_error:
            print("⚠️  Replaced code has syntax errors")
        else:
            print("✅ Replaced code is syntactically correct")
    except Exception as e:
        print(f"⚠️  Error verifying replacement result: {e}")
    
    # Output result
    if output_path:
        output_path.write_bytes(result)
        print(f"Result saved to: {output_path}")
    else:
        print("=== Replaced Code ===")
        print(result.decode('utf-8', errors='replace'))


def main():
    parser = argparse.ArgumentParser(description="Demonstrate tree-sitter node replacement")
    parser.add_argument("input", help="Input Rust file")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--mutations", "-m", type=int, default=16, help="Number of mutations (default: 1)")
    parser.add_argument("--seed", "-s", type=int, default=42, help="Random seed (default: 42)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"File does not exist: {input_path}")
        sys.exit(1)
    
    output_path = Path(args.output) if args.output else None
    
    parse_and_replace(input_path, output_path, args.mutations, args.seed)


if __name__ == "__main__":
    main()