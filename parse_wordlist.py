"""Parse NWL2023.txt to create a clean wordlist"""

def parse_nwl():
    with open('NWL2023.txt', 'r') as infile:
        with open('wordlist.txt', 'w') as outfile:
            for line in infile:
                # Split on first whitespace to separate word from definition
                parts = line.strip().split(None, 1)
                if parts:  # Make sure we have at least one part
                    word = parts[0].strip().upper()
                    if word:  # Make sure we have a non-empty word
                        outfile.write(word + '\n')

if __name__ == '__main__':
    parse_nwl()
    print("Wordlist created successfully!")
