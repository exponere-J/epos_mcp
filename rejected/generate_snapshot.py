import os

def generate_snapshot(output_file="codebase_snapshot.txt"):
    """
    Traverses the current directory and creates a single text file 
    containing the content of all relevant project files.
    """
    
    # Configuration: What to ignore
    IGNORE_DIRS = {
        '.git', '__pycache__', 'venv', 'env', 'node_modules', 
        '.idea', '.vscode', 'build', 'dist', 'egg-info'
    }
    
    # Ignore binary or non-text files that clutter the snapshot
    IGNORE_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.gif', '.ico', 
        '.zip', '.tar', '.gz', '.pdf', 
        '.pyc', '.exe', '.bin', '.so', '.dll', '.db', '.sqlite3'
    }

    # Ignore specific filenames
    IGNORE_FILES = {
        '.DS_Store', 'package-lock.json', 'yarn.lock', output_file
    }

    print(f"[*] Starting codebase snapshot...")
    file_count = 0

    with open(output_file, 'w', encoding='utf-8') as out:
        # Walk through the directory tree
        for root, dirs, files in os.walk("."):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                # Skip ignored files and extensions
                if file in IGNORE_FILES:
                    continue
                if any(file.endswith(ext) for ext in IGNORE_EXTENSIONS):
                    continue

                file_path = os.path.join(root, file)
                
                # Header for each file
                out.write(f"\n{'='*60}\n")
                out.write(f"FILE PATH: {file_path}\n")
                out.write(f"{'='*60}\n")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        out.write(content + "\n")
                        file_count += 1
                except UnicodeDecodeError:
                    out.write("[BINARY OR NON-UTF8 CONTENT - SKIPPED]\n")
                except Exception as e:
                    out.write(f"[ERROR READING FILE: {e}]\n")

    print(f"[+] Snapshot complete! {file_count} files saved to '{output_file}'")

if __name__ == "__main__":
    generate_snapshot()