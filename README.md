# Zeotap-1-Rule_engine


# Rule Management System

The **Rule Management System** is a web-based platform designed to create, combine, and evaluate rules dynamically. Users can input rules, combine them, and test them against user data. The backend processes the rules, evaluates them based on an Abstract Syntax Tree (AST), and returns the results.

## Features

- **Create Rules**: Define rules using simple conditions (e.g., `age > 30`).
- **Combine Rules**: Combine multiple rules using logical operators (AND, OR).
- **Evaluate Rules**: Evaluate rules against user data in JSON format.

## Technologies Used

- **Frontend**: HTML, CSS (Bootstrap), JavaScript (Fetch API).
- **Backend**: Python (Flask), SQLite for database storage.
- **Database**: SQLite (with AST storage in JSON format).
- **Other**: CORS for handling cross-origin requests.

---

## Getting Started

### Prerequisites

Ensure you have the following installed on your system:

- **Python 3.x**: Flask and related packages require Python.
- **SQLite**: The application uses SQLite as the database.


### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/Sathvik-1912/Zeotap-1-Rule_engine.git
   cd Zeotap-1-Rule_engine
   ```

2. **Set up Python Environment**

   Install dependencies by running:

   Install Python dependencies via `pip`:

   ```bash
     pip install flask flask-cors 
   ```


### Running the Application

  

   ```bash
   python rule_engine.py
   ```

   The application will be running at `http://127.0.0.1:5000/`.


---

## Usage Instructions

1. **Create Rule**: Enter a rule (e.g., `age > 30`) and click "Create Rule". The rule will be saved and displayed in the dropdowns.
2. **Combine Rules**: Select multiple rules from the dropdown, click "Combine Rules", and they will be combined with the logical operator (default is AND).
3. **Evaluate Rule**: Select a rule, input user data in JSON format (e.g., `{"age": 25, "salary": 50000}`), and click "Evaluate Rule" to get the result.

---

## Design Choices

1. **Abstract Syntax Tree (AST)**: 
   The AST is used to represent rules in a structured format. This allows us to combine rules and evaluate them efficiently. Python's `ast` module is leveraged for parsing rules.
   
2. **Rule Validation**:
   The application supports only a predefined set of attributes (`age`, `salary`, `experience`, etc.) to ensure security and prevent arbitrary code execution.

3. **SQLite Database**:
   Rules and their corresponding ASTs are stored in an SQLite database. This choice was made due to SQLite's simplicity and zero-configuration setup.

4. **Separation of Concerns**:
   - The **Frontend** handles user interaction (using forms to create, combine, and evaluate rules).
   - The **Backend** processes the rules, stores them, and evaluates them.
   - **Fetch API** is used for communication between the frontend and backend.


## API Endpoints

### 1. **Create Rule**
   - **URL**: `/create_rule`
   - **Method**: POST
   - **Body**: `{ "rule": "<rule_string>" }`
   - **Response**: Returns success or failure message.

### 2. **Get All Rules**
   - **URL**: `/get_rules`
   - **Method**: GET
   - **Response**: List of all available rules.

### 3. **Evaluate Rule**
   - **URL**: `/evaluate_rule`
   - **Method**: POST
   - **Body**: `{ "rule_id": <id>, "data": <user_data> }`
   - **Response**: Result of rule evaluation.

### 4. **Combine Rules**
   - **URL**: `/combine_rules`
   - **Method**: POST
   - **Body**: `{ "rule_ids": [1, 2, 3] }`
   - **Response**: Combined rule and success message.

---

## Dependencies

Make sure the following dependencies are installed:

- Python 3.x
- Flask
- Flask-CORS
- SQLite3

Install Python dependencies via `pip`:

```bash
pip install flask flask-cors sqlite3
```

For frontend:

- **Bootstrap** (via CDN or npm if locally managing assets).

---


