#!/usr/bin/env python3
"""
Security Camera Agent Project Inventory Script
Generates a comprehensive directory listing while respecting .gitignore rules
"""

import os
import pathlib
from datetime import datetime
import fnmatch

def load_gitignore_patterns(root_path):
    """Load patterns from .gitignore file"""
    gitignore_path = os.path.join(root_path, '.gitignore')
    patterns = []
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    patterns.append(line)
    
    return patterns

def should_ignore(path, patterns, root_path):
    """Check if a path should be ignored based on .gitignore patterns"""
    rel_path = os.path.relpath(path, root_path)
    
    # Always ignore .git directory
    if '.git' in rel_path.split(os.sep):
        return True
    
    for pattern in patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith('/'):
            if fnmatch.fnmatch(rel_path + '/', pattern) or \
               fnmatch.fnmatch(os.path.basename(path) + '/', pattern):
                return True
        # Handle file patterns
        else:
            if fnmatch.fnmatch(rel_path, pattern) or \
               fnmatch.fnmatch(os.path.basename(path), pattern):
                return True
    
    return False

def get_file_info(filepath):
    """Get file size and modification time"""
    try:
        stat = os.stat(filepath)
        size = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        return size, mtime
    except:
        return 0, 'unknown'

def generate_tree(root_path, output_file='project_structure.txt'):
    """Generate a tree-like directory structure"""
    
    patterns = load_gitignore_patterns(root_path)
    
    with open(output_file, 'w') as f:
        # Write header
        f.write("=" * 80 + "\n")
        f.write("Security Camera Agent - Project Inventory\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Root Path: {os.path.abspath(root_path)}\n")
        f.write("=" * 80 + "\n\n")
        
        # Collect all items
        items = {'files': [], 'dirs': []}
        
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Filter out ignored directories
            dirnames[:] = [d for d in dirnames 
                          if not should_ignore(os.path.join(dirpath, d), patterns, root_path)]
            
            # Calculate relative path for display
            rel_dir = os.path.relpath(dirpath, root_path)
            if rel_dir == '.':
                rel_dir = ''
            
            # Process directories
            for dirname in sorted(dirnames):
                full_path = os.path.join(dirpath, dirname)
                rel_path = os.path.relpath(full_path, root_path)
                items['dirs'].append(rel_path)
            
            # Process files
            for filename in sorted(filenames):
                full_path = os.path.join(dirpath, filename)
                
                if not should_ignore(full_path, patterns, root_path):
                    rel_path = os.path.relpath(full_path, root_path)
                    size, mtime = get_file_info(full_path)
                    items['files'].append((rel_path, size, mtime))
        
        # Write directory structure
        f.write("DIRECTORY STRUCTURE\n")
        f.write("-" * 80 + "\n\n")
        
        # Group files by directory
        current_dir = None
        all_items = sorted(items['files'], key=lambda x: x[0])
        
        for rel_path, size, mtime in all_items:
            dir_part = os.path.dirname(rel_path)
            file_part = os.path.basename(rel_path)
            
            if dir_part != current_dir:
                current_dir = dir_part
                f.write(f"\n{dir_part if dir_part else '(root)'}/\n")
            
            # Format size
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.1f}KB"
            else:
                size_str = f"{size/(1024*1024):.1f}MB"
            
            f.write(f"  {file_part:<40} {size_str:>10}  {mtime}\n")
        
        # Write summary
        f.write("\n" + "=" * 80 + "\n")
        f.write("SUMMARY\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total Directories: {len(items['dirs'])}\n")
        f.write(f"Total Files: {len(items['files'])}\n")
        
        # File type breakdown
        extensions = {}
        for rel_path, _, _ in items['files']:
            ext = os.path.splitext(rel_path)[1] or '(no extension)'
            extensions[ext] = extensions.get(ext, 0) + 1
        
        f.write(f"\nFile Types:\n")
        for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {ext:<20} {count:>4} files\n")
        
        # Calculate total size
        total_size = sum(size for _, size, _ in items['files'])
        if total_size < 1024:
            size_str = f"{total_size}B"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size/1024:.1f}KB"
        else:
            size_str = f"{total_size/(1024*1024):.2f}MB"
        
        f.write(f"\nTotal Size (tracked files): {size_str}\n")
        
        # List key configuration files found
        f.write(f"\n" + "=" * 80 + "\n")
        f.write("KEY FILES DETECTED\n")
        f.write("-" * 80 + "\n")
        
        key_files = [
            'requirements.txt', 'setup.py', 'pyproject.toml',
            'README.md', 'LICENSE',
            '.env.example', 'config.py', 'config_local.py',
            '*.service', 'Dockerfile', 'docker-compose.yml'
        ]
        
        for rel_path, _, _ in items['files']:
            filename = os.path.basename(rel_path)
            for pattern in key_files:
                if fnmatch.fnmatch(filename, pattern):
                    f.write(f"  {rel_path}\n")
                    break
        
        f.write("\n" + "=" * 80 + "\n")
    
    print(f"Project inventory written to: {output_file}")
    print(f"Total files cataloged: {len(items['files'])}")
    print(f"Total directories: {len(items['dirs'])}")

if __name__ == "__main__":
    import sys
    
    # Use current directory if no path provided
    root_path = sys.argv[1] if len(sys.argv) > 1 else "."
    output_file = sys.argv[2] if len(sys.argv) > 2 else "project_structure.txt"
    
    print(f"Scanning: {os.path.abspath(root_path)}")
    print(f"Output file: {output_file}")
    print("-" * 80)
    
    generate_tree(root_path, output_file)
    
    print("\nDone! You can now upload the project_structure.txt file.")