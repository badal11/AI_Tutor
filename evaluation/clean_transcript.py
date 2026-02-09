import json

def export_all_logs(input_file, output_file):
    print(f"📂 Reading from: {input_file}")
    
    separator = "=" * 50
    count = 0
    
    try:
        with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
            
            # Write Header
            outfile.write("TASK: Evaluate the following model interactions.\n")
            outfile.write("NOTE: This file contains ALL entries from the log.\n\n")
            
            for line_num, line in enumerate(infile, 1):
                if not line.strip():
                    continue

                try:
                    data = json.loads(line.strip())
                    
                    # --- Extract Metadata ---
                    model_name = data.get('model', 'Unknown Model')
                    latency = data.get('latency_seconds', 'N/A')
                    
                    # --- Extract Input (Context) ---
                    input_data = data.get('input')
                    context_text = ""
                    
                    if isinstance(input_data, dict):
                        # Standard Prompt Format
                        sys_prompt = input_data.get('system_prompt', '')
                        usr_prompt = input_data.get('raw_prompt', '') or str(input_data)
                        
                        # Only add System Prompt section if it exists
                        if sys_prompt:
                            context_text += f"--- SYSTEM PROMPT ---\n{sys_prompt}\n\n"
                        context_text += f"--- USER INPUT ---\n{usr_prompt}\n"
                        
                    elif isinstance(input_data, list):
                        # Chat History Format
                        transcript = []
                        for msg in input_data:
                            if isinstance(msg, dict):
                                role = msg.get('role', 'unknown').upper()
                                content = msg.get('content', '')
                                transcript.append(f"[{role}]: {content}")
                        
                        context_text = "--- CONVERSATION HISTORY ---\n" + "\n".join(transcript) + "\n"
                    
                    else:
                        # Fallback for strings or other types
                        context_text = f"--- RAW INPUT ---\n{str(input_data)}\n"

                    # --- Extract Output ---
                    model_output = data.get('output', '')
                    # Pretty print JSON outputs
                    if isinstance(model_output, (dict, list)):
                        model_output = json.dumps(model_output, indent=2)

                    # --- Write Block ---
                    block = (
                        f"{separator}\n"
                        f"SAMPLE #{count + 1} | MODEL: {model_name} | LATENCY: {latency}s\n"
                        f"{separator}\n"
                        f"{context_text}\n"
                        f"--- MODEL OUTPUT ---\n"
                        f"{model_output}\n\n"
                    )
                    
                    outfile.write(block)
                    count += 1
                    
                except json.JSONDecodeError:
                    print(f"❌ Line {line_num}: Skipped (Invalid JSON)")
                    continue
                    
        print("\n" + "="*30)
        print(f"✅ Successfully exported {count} entries to '{output_file}'")
        print("="*30)

    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")

if __name__ == "__main__":
    export_all_logs('evaluation/logs.jsonl', 'judge_dataset.txt')