import os

def bundle_filtered_python(output_file="project_context.txt"):
    # List of specific files to ignore
    ignore_files = {
        "test.py", 
        "for-report.py", 
        "larger-models.py", 
        "code_dumper.py",
        output_file
    }

    count = 0
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for root, dirs, files in os.walk("."):
            # Ignore hidden directories (like .git) and virtual environments
            dirs[:] = [d for d in dirs if not d.startswith(('.', 'venv', 'env'))]
            
            for file in files:
                # Rule 1: Must be a .py file
                # Rule 2: Must NOT be in our ignore list
                if file.endswith(".py") and file not in ignore_files:
                    file_path = os.path.join(root, file)
                    
                    f_out.write(f"\n# {'='*5} LOCATION: {file_path} {'='*5}\n")
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f_in:
                            f_out.write(f_in.read())
                        count += 1
                    except Exception as e:
                        f_out.write(f"# [Error reading file {file}: {e}]\n")
                    
                    f_out.write(f"\n# {'='*5} END OF {file} {'='*5}\n")

    print(f"Done! Bundled {count} Python files into '{output_file}'.")

if __name__ == "__main__":
    bundle_filtered_python()