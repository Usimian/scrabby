import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random
import string
from functools import partial
import json
import itertools

class ScrabbyGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Scrabby - Word Game")
        self.root.geometry("1200x800")
        
        # Score and current word variables
        self.score = 0
        self.current_word = ""
        self.selected_letter = None
        
        # Load word list
        self.valid_words = set()
        try:
            with open('wordlist.txt', 'r') as f:
                self.valid_words = set(word.strip().upper() for word in f if len(word.strip()) >= 2)
            print(f"Loaded {len(self.valid_words)} valid words")
        except FileNotFoundError:
            messagebox.showerror("Error", "Scrabble word list not found. Please ensure wordlist.txt is in the same directory.")
            self.root.quit()
        
        # Board size and square size
        self.BOARD_SIZE = 15
        self.SQUARE_SIZE = 45
        
        # Special squares configuration
        self.special_squares = {
            'TW': [(0,0), (0,7), (0,14), (7,0), (7,14), (14,0), (14,7), (14,14)],  # Triple Word
            'DW': [(1,1), (2,2), (3,3), (4,4), (13,13), (12,12), (11,11), (10,10), 
                   (1,13), (2,12), (3,11), (4,10), (13,1), (12,2), (11,3), (10,4)],  # Double Word
            'TL': [(1,5), (1,9), (5,1), (5,5), (5,9), (5,13), (9,1), (9,5), (9,9), (9,13), (13,5), (13,9)],  # Triple Letter
            'DL': [(0,3), (0,11), (2,6), (2,8), (3,0), (3,7), (3,14), (6,2), (6,6), (6,8), (6,12),
                   (7,3), (7,11), (8,2), (8,6), (8,8), (8,12), (11,0), (11,7), (11,14), (12,6), (12,8), (14,3), (14,11)]  # Double Letter
        }
        
        # Letter scores (simplified version)
        self.letter_scores = {letter: 1 for letter in string.ascii_uppercase}
        for letter in 'AEILNORSTU':
            self.letter_scores[letter] = 1
        for letter in 'DG':
            self.letter_scores[letter] = 2
        for letter in 'BCMP':
            self.letter_scores[letter] = 3
        for letter in 'FHVWY':
            self.letter_scores[letter] = 4
        for letter in 'K':
            self.letter_scores[letter] = 5
        for letter in 'JX':
            self.letter_scores[letter] = 8
        for letter in 'QZ':
            self.letter_scores[letter] = 10

        self.setup_ui()
        self.generate_new_letters()

    def setup_ui(self):
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Left panel for score and rack
        self.left_panel = ttk.Frame(self.main_frame)
        self.left_panel.grid(row=0, column=0, padx=10, sticky="nsew")

        # Score frame
        score_frame = ttk.Frame(self.left_panel)
        score_frame.grid(row=0, column=0, pady=10, sticky="ew")
        
        # Total score display
        total_score_label = ttk.Label(
            score_frame,
            text="Total Score:",
            font=('Helvetica', 14)
        )
        total_score_label.grid(row=0, column=0, padx=5)
        
        self.score_label = ttk.Label(
            score_frame,
            text="0",
            font=('Helvetica', 24, 'bold')
        )
        self.score_label.grid(row=0, column=1, padx=5)

        # Best possible word frame
        best_word_frame = ttk.Frame(self.left_panel)
        best_word_frame.grid(row=1, column=0, pady=5, sticky="nsew")
        best_word_frame.grid_columnconfigure(0, weight=1)
        best_word_frame.grid_rowconfigure(1, weight=1)

        best_word_label = ttk.Label(
            best_word_frame,
            text="Possible Words:",
            font=('Helvetica', 12)
        )
        best_word_label.grid(row=0, column=0, padx=5, sticky='w')

        # Create Treeview with scrollbar
        tree_frame = ttk.Frame(best_word_frame)
        tree_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # Create Treeview
        self.word_tree = ttk.Treeview(
            tree_frame,
            columns=('word', 'score'),
            show='headings',
            height=8
        )
        self.word_tree.heading('word', text='Word')
        self.word_tree.heading('score', text='Score')
        self.word_tree.column('word', width=100)
        self.word_tree.column('score', width=50)
        self.word_tree.grid(row=0, column=0, sticky='nsew')

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient='vertical',
            command=self.word_tree.yview
        )
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.word_tree.configure(yscrollcommand=scrollbar.set)

        # Legend frame
        legend_frame = ttk.LabelFrame(self.left_panel, text="Special Squares", padding="10")
        legend_frame.grid(row=2, column=0, pady=10, sticky="ew")
        
        # Legend entries
        legend_entries = [
            ("TW", "Triple Word", "#ff9999"),
            ("DW", "Double Word", "#ffb366"),
            ("TL", "Triple Letter", "#99ff99"),
            ("DL", "Double Letter", "#99ccff")
        ]
        
        for idx, (code, text, color) in enumerate(legend_entries):
            square = tk.Canvas(legend_frame, width=30, height=30, bg=color)
            square.grid(row=idx, column=0, padx=5, pady=2)
            ttk.Label(legend_frame, text=f"{code} - {text}").grid(row=idx, column=1, padx=5, pady=2, sticky="w")

        # Letter tiles frame (rack)
        self.tiles_frame = ttk.Frame(self.left_panel)
        self.tiles_frame.grid(row=3, column=0, pady=20)

        # Buttons frame
        self.buttons_frame = ttk.Frame(self.left_panel)
        self.buttons_frame.grid(row=4, column=0, pady=20)

        # Submit and Clear buttons
        self.submit_button = ttk.Button(
            self.buttons_frame,
            text="Submit Word",
            command=self.submit_word
        )
        self.submit_button.grid(row=0, column=0, padx=5)

        self.clear_button = ttk.Button(
            self.buttons_frame,
            text="Clear Word",
            command=self.clear_word
        )
        self.clear_button.grid(row=0, column=1, padx=5)

        # Save/Load buttons
        save_load_frame = ttk.Frame(self.buttons_frame)
        save_load_frame.grid(row=1, column=0, columnspan=2, pady=10)

        self.save_button = ttk.Button(
            save_load_frame,
            text="Save Game",
            command=self.save_game
        )
        self.save_button.grid(row=0, column=0, padx=5)

        self.load_button = ttk.Button(
            save_load_frame,
            text="Load Game",
            command=self.load_game
        )
        self.load_button.grid(row=0, column=1, padx=5)

        self.clear_game_button = ttk.Button(
            save_load_frame,
            text="Clear Game",
            command=self.clear_game
        )
        self.clear_game_button.grid(row=0, column=2, padx=5)

        # Board frame (center panel)
        self.board_frame = ttk.Frame(self.main_frame)
        self.board_frame.grid(row=0, column=1, padx=10, sticky="nsew")
        
        # Create the board
        self.board_squares = []
        for i in range(self.BOARD_SIZE):
            row = []
            for j in range(self.BOARD_SIZE):
                square_frame = tk.Frame(
                    self.board_frame,
                    width=self.SQUARE_SIZE,
                    height=self.SQUARE_SIZE,
                    relief="raised",
                    borderwidth=1
                )
                square_frame.grid(row=i, column=j, padx=1, pady=1)
                square_frame.grid_propagate(False)
                
                # Add background for special squares
                bg_color = self.get_square_color(i, j)
                square_frame.configure(bg=bg_color)
                
                # Create a StringVar to store the entry's value
                var = tk.StringVar()
                var.trace('w', lambda *args, v=var, r=i, c=j: self.on_square_edit(v, r, c))
                
                # Create the entry widget
                entry = tk.Entry(
                    square_frame,
                    width=2,
                    font=('Helvetica', 16, 'bold'),
                    justify='center',
                    bg=bg_color,
                    textvariable=var,
                    relief='flat',
                    highlightthickness=0
                )
                entry.place(relx=0.5, rely=0.35, anchor="center")
                
                # Bind event to force uppercase
                entry.bind('<KeyRelease>', lambda e, v=var: self.force_uppercase(v))
                
                # Create score label
                score_label = tk.Label(
                    square_frame,
                    text="",
                    font=('Helvetica', 9),
                    bg=bg_color,
                    fg='#444444'
                )
                score_label.place(relx=0.5, rely=0.75, anchor="center")
                
                # Store both the frame and entry widget
                row.append({
                    'frame': square_frame,
                    'entry': entry,
                    'score_label': score_label,
                    'var': var,
                    'letter': None
                })
            self.board_squares.append(row)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=3)
        self.main_frame.columnconfigure(0, weight=1)

    def get_square_color(self, row, col):
        pos = (row, col)
        if pos in self.special_squares['TW']:
            return "#ff9999"  # Red for Triple Word
        elif pos in self.special_squares['DW']:
            return "#ffb366"  # Pink for Double Word
        elif pos in self.special_squares['TL']:
            return "#99ff99"  # Green for Triple Letter
        elif pos in self.special_squares['DL']:
            return "#99ccff"  # Blue for Double Letter
        return "#f8f9fa"  # Default color

    def force_uppercase(self, var):
        """Force the entry content to be uppercase"""
        current = var.get()
        if current != current.upper():
            var.set(current.upper())

    def save_game(self):
        """Save the current game state to a JSON file"""
        # Create game state dictionary
        game_state = {
            'score': self.score,
            'board_state': {},
            'rack_letters': []
        }

        # Save board state
        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                letter = self.board_squares[row][col]['var'].get()
                if letter:
                    game_state['board_state'][f"{row},{col}"] = letter

        # Save rack letters
        for widget in self.tiles_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                entry = widget.grid_slaves(row=0, column=0)[0]
                letter = entry.get()
                game_state['rack_letters'].append(letter)

        # Ask user where to save the file
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile="scrabby_save.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    # Save in a pretty-printed, human-readable format
                    json.dump(game_state, f, indent=4)
                messagebox.showinfo("Success", "Game saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save game: {str(e)}")

    def load_game(self):
        """Load a previously saved game state"""
        filename = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt")],
            title="Load Game State"
        )
        
        if not filename:
            return

        try:
            with open(filename, 'r') as f:
                game_state = json.load(f)

            # Clear current game state
            self.clear_board()
            self.clear_rack()
            
            # Restore score
            self.score = game_state['score']
            self.score_label.config(text=str(self.score))
            
            # Restore board state
            for pos, letter in game_state['board_state'].items():
                row, col = map(int, pos.split(','))
                self.board_squares[row][col]['var'].set(letter)
                self.board_squares[row][col]['letter'] = letter
                self.board_squares[row][col]['score_label'].config(text=str(self.letter_scores[letter]))
            
            # Restore rack letters
            self.letter_vars = []
            for i, letter in enumerate(game_state['rack_letters']):
                score = self.letter_scores[letter]
                letter_var = tk.StringVar(value=letter)
                self.letter_vars.append(letter_var)
                
                tile_frame = ttk.Frame(self.tiles_frame)
                tile_frame.grid(row=0, column=i, padx=2)

                entry = ttk.Entry(
                    tile_frame,
                    textvariable=letter_var,
                    width=2,
                    justify='center',
                    font=('Helvetica', 14, 'bold')
                )
                entry.grid(row=0, column=0)

                score_label = ttk.Label(
                    tile_frame,
                    text=str(score),
                    font=('Helvetica', 10)
                )
                score_label.grid(row=1, column=0)
                
            # messagebox.showinfo("Success", "Game loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load game: {str(e)}")

    def clear_board(self):
        """Clear all letters from the board"""
        for row in self.board_squares:
            for square in row:
                square['var'].set('')
                square['letter'] = None
                square['score_label'].config(text="")

    def clear_rack(self):
        """Clear all letters from the rack"""
        for widget in self.tiles_frame.winfo_children():
            widget.destroy()

    def calculate_word_score(self, word):
        """Calculate the score for a word, including special square multipliers"""
        if not word:
            return 0
            
        # First find all letters on the board
        letters_with_positions = []
        for i in range(self.BOARD_SIZE):
            for j in range(self.BOARD_SIZE):
                letter = self.board_squares[i][j]['var'].get()
                if letter:
                    letters_with_positions.append((letter, i, j))
        
        if not letters_with_positions:
            return 0
            
        # Calculate base score with letter multipliers
        base_score = 0
        word_multiplier = 1
        
        for letter, row, col in letters_with_positions:
            letter_score = self.letter_scores[letter]
            pos = (row, col)
            
            # Apply letter multipliers
            if pos in self.special_squares['TL']:
                letter_score *= 3
            elif pos in self.special_squares['DL']:
                letter_score *= 2
                
            base_score += letter_score
            
            # Track word multipliers
            if pos in self.special_squares['TW']:
                word_multiplier *= 3
            elif pos in self.special_squares['DW']:
                word_multiplier *= 2
        
        # Apply word multipliers
        final_score = base_score * word_multiplier
        
        return final_score

    def on_square_edit(self, var, row, col):
        """Handle editing of a square's content"""
        value = var.get().upper()
        square = self.board_squares[row][col]
        
        # If the value is empty, clear the square
        if not value:
            square['letter'] = None
            square['score_label'].config(text="")
            return
            
        # Only allow single letters
        if len(value) > 1:
            # Keep only the first letter
            value = value[0].upper()
            var.set(value)
            
        # Ensure it's a letter
        if not value.isalpha():
            var.set('')
            square['score_label'].config(text="")
            return
            
        # Update the square's letter and score
        square['letter'] = value
        square['score_label'].config(text=str(self.letter_scores[value]))

    def add_letter(self, letter):
        """When a rack letter is clicked, find the first empty square and place the letter there"""
        letter = letter.upper()  # Ensure uppercase
        for i in range(self.BOARD_SIZE):
            for j in range(self.BOARD_SIZE):
                square = self.board_squares[i][j]
                if not square['var'].get():
                    square['var'].set(letter)
                    square['letter'] = letter
                    square['score_label'].config(text=str(self.letter_scores[letter]))
                    return

    def clear_word(self):
        """Clear all squares on the board"""
        self.current_word = ""
        # Clear the board
        for row in self.board_squares:
            for square in row:
                square['var'].set('')
                square['letter'] = None
                square['score_label'].config(text="")

    def get_current_word(self):
        """Get all letters on the board as a word"""
        word = ""
        for i in range(self.BOARD_SIZE):
            for j in range(self.BOARD_SIZE):
                letter = self.board_squares[i][j]['var'].get()
                if letter:
                    word += letter
        return word

    def submit_word(self):
        """Submit the current word on the board"""
        word = self.get_current_word()
        if len(word) >= 2:
            # Calculate score for the word
            word_score = self.calculate_word_score(word)
            self.score += word_score
            self.score_label.config(text=str(self.score))
            self.clear_word()
            self.generate_new_letters()

    def generate_new_letters(self):
        # Clear existing tiles
        for widget in self.tiles_frame.winfo_children():
            widget.destroy()

        # Generate 7 random letters (already uppercase)
        vowels = 'AEIOU'
        consonants = 'BCDFGHJKLMNPQRSTVWXYZ'
        letters = random.choices(vowels, k=3) + random.choices(consonants, k=4)
        random.shuffle(letters)

        # Create letter tiles
        self.letter_vars = []
        for i, letter in enumerate(letters):
            # Create frame for letter and score
            tile_frame = ttk.Frame(self.tiles_frame)
            tile_frame.grid(row=0, column=i, padx=2)

            # Create StringVar for the letter
            letter_var = tk.StringVar(value=letter)
            self.letter_vars.append(letter_var)
            letter_var.trace('w', lambda *args, var=letter_var: self.on_rack_letter_change(var))

            # Create entry for letter
            entry = ttk.Entry(
                tile_frame,
                textvariable=letter_var,
                width=2,
                justify='center',
                font=('Helvetica', 14, 'bold')
            )
            entry.grid(row=0, column=0)

            # Create label for score
            score_label = ttk.Label(
                tile_frame,
                text=str(self.letter_scores.get(letter, 0)),
                font=('Helvetica', 10)
            )
            score_label.grid(row=1, column=0)

    def on_rack_letter_change(self, var):
        """Handle changes to rack letters"""
        value = var.get().upper()
        if len(value) > 1:
            var.set(value[-1])  # Keep only the last character
            return
        
        if value and not value.isalpha():
            var.set('')  # Clear non-letter characters
            return

        var.set(value.upper())
        
        # Update score label if it exists
        for widget in self.tiles_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                entry = widget.grid_slaves(row=0, column=0)[0]
                if entry.cget('textvariable') == str(var):
                    score_label = widget.grid_slaves(row=1, column=0)[0]
                    score_label.config(text=str(self.letter_scores.get(value, 0)))
        
        # Update best possible word
        self.update_best_word()

    def update_best_word(self):
        """Calculate and display all possible words from rack letters"""
        # Get current rack letters
        rack_letters = []
        for widget in self.tiles_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                entry = widget.grid_slaves(row=0, column=0)[0]
                letter = entry.get().upper()
                if letter:
                    rack_letters.append(letter)

        # Clear existing items
        for item in self.word_tree.get_children():
            self.word_tree.delete(item)

        if not rack_letters:
            return

        # Create a letter frequency map for our rack
        letter_freq = {}
        for letter in rack_letters:
            letter_freq[letter] = letter_freq.get(letter, 0) + 1

        # Find all possible words and their scores
        possible_words = []
        
        # Check each word in our dictionary
        for word in self.valid_words:
            # Skip words longer than our rack
            if len(word) > len(rack_letters):
                continue
                
            # Check if we can make this word with our letters
            word_freq = {}
            for letter in word:
                word_freq[letter] = word_freq.get(letter, 0) + 1
                
            can_make_word = True
            for letter, count in word_freq.items():
                if letter not in letter_freq or letter_freq[letter] < count:
                    can_make_word = False
                    break
                    
            if can_make_word:
                score = sum(self.letter_scores[letter] for letter in word)
                possible_words.append((word, score))

        # Sort by score (descending)
        possible_words.sort(key=lambda x: (-x[1], x[0]))

        # Update display
        for word, score in possible_words:
            self.word_tree.insert('', 'end', values=(word, score))

    def is_valid_word(self, word):
        """Check if a word is valid using the loaded word list"""
        return word.upper() in self.valid_words

    def clear_game(self):
        """Reset the entire game state"""
        # Clear the board
        self.clear_board()
        # Clear the rack
        self.clear_rack()
        # Reset score
        self.score = 0
        self.score_label.config(text="0")
        # Generate new letters
        self.generate_new_letters()
        self.update_best_word()

def main():
    root = tk.Tk()
    app = ScrabbyGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()
