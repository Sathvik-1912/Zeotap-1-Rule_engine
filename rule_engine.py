import sqlite3
import json
from flask import Flask, request, jsonify
from datetime import datetime
from flask_cors import CORS
import ast

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


VALID_ATTRIBUTES = {'age', 'department', 'salary', 'experience'}

class Node:
    def __init__(self, node_type: str, left=None, right=None, value=None):
        self.type = node_type 
        self.left = left  
        self.right = right 
        self.value = value  

    def __repr__(self):
        return f'Node(type={self.type}, value={self.value})'


def build_ast(tree_node) -> Node:
    if isinstance(tree_node, ast.BoolOp):
        op = "AND" if isinstance(tree_node.op, ast.And) else "OR"
        node = Node("operator", value=op)
        node.left = build_ast(tree_node.values[0])
        node.right = build_ast(tree_node.values[1])
        return node
    elif isinstance(tree_node, ast.Compare):
   
        left = ast.dump(tree_node.left)
        operator = ast.dump(tree_node.ops[0])
        right = ast.dump(tree_node.comparators[0])
        return Node("operand", value=f"{left} {operator} {right}")
    else:
        raise ValueError("Unsupported AST node type")


def parse_rule_to_ast(rule_string: str) -> Node:
    tree = ast.parse(rule_string, mode='eval')
    return build_ast(tree.body)


def validate_rule_string(rule_string: str) -> bool:
    for attr in VALID_ATTRIBUTES:
        if attr in rule_string:
            return True
    return False

def save_rule(rule_string: str, ast: Node):
    conn = sqlite3.connect('rules.db')
    c = conn.cursor()
    ast_json = json.dumps(ast, default=lambda o: o.__dict__)
    c.execute("INSERT INTO rules (rule_string, ast, created_at) VALUES (?, ?, ?)",
              (rule_string, ast_json, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_all_rules():
    conn = sqlite3.connect('rules.db')
    c = conn.cursor()
    c.execute("SELECT id, rule_string FROM rules")
    rules = [{"id": row[0], "rule_string": row[1]} for row in c.fetchall()]
    conn.close()
    return rules


def evaluate_rule(ast: Node, data: dict) -> bool:
    try:
        rule_string = ast.value
        safe_globals = {"custom_function": custom_function} 
        return eval(rule_string, safe_globals, data)
    except (SyntaxError, NameError, ValueError) as e:
        print(f"Error evaluating rule: {e}")
        return False


def combine_rules(rule_strings, combine_operator="AND"):
    ast_nodes = [parse_rule_to_ast(rule) for rule in rule_strings]
    combined_operator = "AND" if combine_operator.upper() == "AND" else "OR"

    if len(ast_nodes) == 1:
        return ast_nodes[0]

    combined_ast = Node("operator", value=combined_operator, left=ast_nodes[0], right=ast_nodes[1])
    for i in range(2, len(ast_nodes)):
        combined_ast = Node("operator", value=combined_operator, left=combined_ast, right=ast_nodes[i])

    return combined_ast


def modify_rule_operator(ast_node: Node, new_operator: str):
    if ast_node.type == 'operator':
        ast_node.value = new_operator 
    else:
        raise ValueError("The node is not an operator")

def modify_rule_operand(ast_node: Node, new_value: str):
    if ast_node.type == 'operand':
        ast_node.value = new_value 
    else:
        raise ValueError("The node is not an operand")

def setup_db():
    conn = sqlite3.connect('rules.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rules 
                 (id INTEGER PRIMARY KEY, rule_string TEXT, ast TEXT, created_at TEXT)''')
    conn.commit()
    conn.close()


def custom_function(x):
    return x > 1000


@app.route('/create_rule', methods=['POST'])
def create_rule_api():
    rule_string = request.json.get('rule')
    if not rule_string:
        return jsonify({'error': 'Rule string is required'}), 400

  
    if not validate_rule_string(rule_string):
        return jsonify({'error': 'Invalid attributes in rule'}), 400

    try:
        ast_node = parse_rule_to_ast(rule_string)
        save_rule(rule_string, ast_node)
        return jsonify({'message': 'Rule created successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_rules', methods=['GET'])
def get_rules_api():
    try:
        rules = get_all_rules()
        return jsonify({'rules': rules}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/evaluate_rule', methods=['POST'])
def evaluate_rule_api():
    rule_id = request.json.get('rule_id')
    user_data = request.json.get('data')

    if not isinstance(rule_id, int) or rule_id <= 0:
        return jsonify({'error': 'Invalid rule ID'}), 400
    if not isinstance(user_data, dict):
        return jsonify({'error': 'User data must be a dictionary'}), 400

    try:
        user_data['age'] = int(user_data['age'])
        user_data['salary'] = float(user_data['salary'])
        user_data['experience'] = int(user_data['experience'])
    except ValueError as e:
        return jsonify({'error': f"Data type error: {str(e)}"}), 400

    conn = sqlite3.connect('rules.db')
    c = conn.cursor()
    c.execute("SELECT ast FROM rules WHERE id = ?", (rule_id,))
    row = c.fetchone()
    conn.close()

    if row:
        ast_node = json.loads(row[0], object_hook=lambda d: Node(d['type'], d.get('left'), d.get('right'), d.get('value')))
        try:
            result = evaluate_rule(ast_node, user_data)
            return jsonify({'result': result}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Rule not found'}), 404

@app.route('/combine_rules', methods=['POST'])
def combine_rules_api():
    try:
        rule_ids = request.json.get('rule_ids')
        if not rule_ids or not isinstance(rule_ids, list):
            return jsonify({'error': 'Invalid input. rule_ids must be a list of integers.'}), 400

        conn = sqlite3.connect('rules.db')
        c = conn.cursor()
        placeholders = ','.join('?' for _ in rule_ids)
        query = f"SELECT rule_string FROM rules WHERE id IN ({placeholders})"
        c.execute(query, rule_ids)
        rows = c.fetchall()
        conn.close()

        if not rows:
            return jsonify({'error': 'No rules found for the provided rule IDs.'}), 404

        rule_strings = [row[0] for row in rows]
        combined_ast = combine_rules(rule_strings)  
        combined_rule_string = " AND ".join(rule_strings)  

   
        combined_ast_json = json.dumps(combined_ast, default=lambda o: o.__dict__)
        conn = sqlite3.connect('rules.db')
        c = conn.cursor()
        c.execute("INSERT INTO rules (rule_string, ast, created_at) VALUES (?, ?, ?)",
                  (combined_rule_string, combined_ast_json, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        return jsonify({'combined_rule': combined_rule_string, 'message': 'Combined rule created and saved successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    setup_db() 
    app.run(debug=True)
