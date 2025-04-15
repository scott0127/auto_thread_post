# Thread Auto

Thread Auto is a Python application that allows users to create and publish posts to Threads easily. The application features a user-friendly interface for taking notes and supports real-time saving of notes.

## Project Structure

```
thread_auto
├── main.py                # Main logic for interacting with the Threads API
├── ui
│   ├── app.py            # Entry point for the user interface
│   └── templates
│       └── index.html    # HTML template for the user interface
├── static
│   └── style.css         # CSS styles for the user interface
├── requirements.txt       # List of dependencies
└── README.md              # Documentation for the project
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd thread_auto
   ```

2. **Install dependencies:**
   Make sure you have Python installed. Then, run:
   ```
   pip install -r requirements.txt
   ```

3. **Run the application:**
   Start the user interface by running:
   ```
   python ui/app.py
   ```

4. **Access the application:**
   Open your web browser and go to `http://127.0.0.1:5000` to access the user interface.

## Usage Guidelines

- Use the text area to write your notes.
- Click the "Save" button to save your notes in real-time.
- Click the "Publish" button to send your notes as a post to Threads.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.