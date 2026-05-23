import json
import re
import requests

def clean_gutenberg_text(raw_text):
    """
    Strips the standard Project Gutenberg legal headers and footers 
    from a raw downloaded text string.
    """
    # Common landmark phrases indicating the start of the actual book content
    start_patterns = [
        r"\*\*\* START OF TH(E|IS) PROJECT GUTENBERG EBOOK .* \*\*\*",
        r"\*\*\*START OF TH(E|IS) PROJECT GUTENBERG EBOOK .* \*\*\*",
        r"START OF THE PROJECT GUTENBERG EBOOK",
        r"*** START OF USER COMMENTS ***"
    ]
    
    # Common landmark phrases indicating the end of the book content
    end_patterns = [
        r"\*\*\* END OF TH(E|IS) PROJECT GUTENBERG EBOOK .* \*\*\*",
        r"\*\*\*END OF TH(E|IS) PROJECT GUTENBERG EBOOK .* \*\*\*",
        r"END OF THE PROJECT GUTENBERG EBOOK",
        r"*** END OF USER COMMENTS ***"
    ]
    
    start_index = 0
    end_index = len(raw_text)
    
    # 1. Search for the beginning of the story
    for pattern in start_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            start_index = match.end()
            break
            
    # 2. Search for the end of the story
    for pattern in end_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            end_index = match.start()
            break
            
    # 3. Slice and remove extra whitespace padding
    return raw_text[start_index:end_index].strip()


class OnlineLibraryManager:
    def __init__(self, config_path="library.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.api_config = self.config.get("api_configuration", {})
        
    def load_config(self):
        """Loads the library configuration file containing target IDs."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error: {self.config_path} file not found. Make sure it is in the same folder!")
            return {}

    def fetch_featured_stories(self):
        """Fetches catalog data from Gutendex using the IDs stored in library.json."""
        ids = self.config.get("featured_story_ids", [])
        if not ids:
            print("No story IDs found in the configuration.")
            return []
            
        # Converts list [11, 84] to string "11,84" for the web query
        id_string = ",".join(map(str, ids))
        base_url = self.api_config.get('base_url', 'https://gutendex.com/books/')
        url = f"{base_url}?ids={id_string}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except requests.RequestException as e:
            print(f"Failed to connect to the public library catalog: {e}")
            return []

    def get_story_content(self, text_url):
        """Downloads the text of a book and runs it through the cleanup filter."""
        if not text_url:
            return "No text link available for this book."
            
        try:
            response = requests.get(text_url)
            response.raise_for_status()
            
            # Download full file text
            raw_text = response.text
            
            # Clean out the legal licensing lines
            cleaned_text = clean_gutenberg_text(raw_text)
            return cleaned_text
            
        except requests.RequestException as e:
            return f"Could not load the story text. Please check your connection. (Error: {e})"


# --- TESTING THE COMPLETE CONNECTION WORKFLOW ---
if __name__ == "__main__":
    # Make sure you have run: pip install requests
    
    # 1. Initialize the system
    library = OnlineLibraryManager()

    print("Connecting to Project Gutenberg via Gutendex API...")
    featured_books = library.fetch_featured_stories()

    # 2. Display the live online catalog to the screen
    print("\n--- Available Public Library Stories ---")
    if not featured_books:
        print("Could not retrieve catalog. Check your internet connection or library.json.")
    else:
        for index, book in enumerate(featured_books):
            author_name = book['authors'][0]['name'] if book['authors'] else 'Unknown Author'
            print(f"[{index}] {book['title']} by {author_name}")

        # 3. Choose the first book from the downloaded list to read
        selected_index = 0 
        target_book = featured_books[selected_index]
        
        # Grab the text/plain link from the formats block
        formats = target_book.get("formats", {})
        text_link = formats.get("text/plain; charset=utf-8") or formats.get("text/plain")
        
        print(f"\nDownloading and cleaning text for: '{target_book['title']}'...")
        story_content = library.get_story_content(text_link)
        
        print("\n--- Cleaned Story Sample (First 400 Characters) ---")
        print(story_content[:400] + "\n...")
