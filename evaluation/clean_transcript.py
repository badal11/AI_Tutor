import json

def generate_minimal_transcripts(log_file_path, output_file_path):
    transcripts = []
    
    with open(log_file_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            # --- FILTER LOGIC ---
            # 1. Skip Llama validators (type: json_gen + model: llama)
            model_name = data.get("model", "").lower()
            msg_type = data.get("type", "")
            
            if msg_type == "json_gen" and "llama" in model_name:
                continue

            # --- DATA EXTRACTION ---
            input_data = data.get("input", {})
            
            # Extract user topic (handling both dict and list input types)
            if isinstance(input_data, dict):
                user_request = input_data.get("topic", "N/A")
            elif isinstance(input_data, list) and len(input_data) > 0:
                # For chat-style logs, get the last user message
                user_request = input_data[-1].get("content", "N/A")
            else:
                user_request = str(input_data)

            output_content = data.get("output", "N/A")

            # --- TRANSCRIPT FORMATTING ---
            # We omit system_prompt here to keep it clean for the judge
            clean_entry = (
                f"### NEW TRANSCRIPT ###\n"
                f"**Target Model:** {data.get('model')}\n"
                f"**User Topic:** {user_request}\n"
                f"**Generated Response:**\n"
                f"```json\n"
                f"{json.dumps(output_content, indent=2) if isinstance(output_content, dict) else output_content}\n"
                f"```\n"
                f"--- END OF ENTRY ---\n\n"
            )
            transcripts.append(clean_entry)

    with open(output_file_path, 'w') as f:
        f.writelines(transcripts)
    
    print(f"Success! Cleaned transcript saved to: {output_file_path}")

# Usage
generate_minimal_transcripts('evaluation/logs.jsonl', 'judge_ready_transcript.txt')