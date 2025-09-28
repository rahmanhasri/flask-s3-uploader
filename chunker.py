import os
import json

def chunk_urls(filename, chunk_size=100):
    url_chunks = []
    current_chunk = []
    basenames = []
    
    with open(filename, 'r') as file:
        for line in file:
            url = line.strip()
            if url:  # Skip empty lines
                current_chunk.append(url)

                if len(current_chunk) == chunk_size:
                    url_chunks.append(json.dumps(current_chunk))
                    basenames.append(json.dumps([os.path.basename(url) for url in current_chunk]))
                    current_chunk = []

    # Add remaining URLs if any
    if current_chunk:
        # append as json
        json_chunk = json.dumps(current_chunk)
        url_chunks.append(json_chunk)
        basenames.append(json.dumps([os.path.basename(url) for url in current_chunk]))

    return [url_chunks, basenames]


# Usage:
result = chunk_urls('url_category.csv')
