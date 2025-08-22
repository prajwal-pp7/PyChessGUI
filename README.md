# Advanced Chess Application

This is a GUI-based chess application built with Python and the Pygame library. 
It features a modern, user-friendly interface with different game modes, including 
Human vs. Human, Human vs. AI, and AI vs. AI. The application utilizes a powerful 
chess engine for game analysis and an AI opponent, offers customizable themes, 
and includes features like time tracking, hints, and game saving.

---

## Features

- **Interactive Data Visualization**  
  Visualize chess moves and positions using an intuitive GUI.  
  ----

- **Multiple Game Modes**  
  Play Human vs. Human, Human vs. AI, or AI vs. AI.  
  ----

- **AI Opponent with Stockfish**  
  Integrated Stockfish engine provides strong AI moves and analysis.  
  ----

- **Customizable Themes**  
  Switch between different board and piece themes.  
  ----

- **Time Tracking**  
  Play with timers for competitive chess matches.  
  ----

- **Hints and Move Suggestions**  
  Get hints from the engine when you are stuck.  
  ----

- **Game Saving**  
  Save and load games for later analysis or continuation.  
  ----

---

## Prerequisites

To run this application, you must have the following installed:

### 1. Python 3.x
Ensure you have a modern version of Python installed on your system.

### 2. Python Libraries
Install the required Python libraries using `pip`. Open your terminal or command prompt and run:

```bash
pip install pygame
pip install python-chess
```

### 3. Stockfish Chess Engine
The AI functionality of this application is powered by the Stockfish chess engine. 
You must download the correct executable for your operating system and place it directly inside your project folder.

**Download Link:** [Download Stockfish](https://stockfishchess.org/download/)

After downloading, rename the executable to match the name used in the code. 
For example, for Windows, the file name should be `stockfish-windows-x86-64-avx2.exe`.

---

## Project Structure

Ensure your project directory contains the following files and folders:

```
/your-project-folder
├── final.py
├── stockfish-windows-x86-64-avx2.exe
├── sounds/
│   ├── move.wav
│   └── capture.wav
├── pieces/
│   ├── bB.png
│   ├── bK.png
│   ├── bN.png
│   ├── bP.png
│   ├── bQ.png
│   ├── bR.png
│   ├── wB.png
│   ├── wK.png
│   ├── wN.png
│   ├── wP.png
│   ├── wQ.png
│   └── wR.png
└── user_data.json (auto-generated on first run)
```

---

## How to Run the Application

Follow these simple steps to start the chess game:

1. Open your terminal or command prompt.
2. Navigate to the project directory using the `cd` command:

```bash
cd /path/to/your-project-folder
```

Example (Windows):
```bash
cd C:\Users\YourName\Downloads\check
```

3. Run the script:

```bash
python final.py
```

The application window should appear, and you can begin playing chess!
