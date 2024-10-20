import sqlite3
import json
from flask import Flask, request, jsonify, render_template
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
        left = tree_node.left.id
        operator = tree_node.ops[0]

        if isinstance(operator, ast.Gt):
            op = '>'
        elif isinstance(operator, ast.Lt):
            op = '<'
        elif isinstance(operator, ast.Eq):
            op = '=='
        else:
            raise ValueError(f"Unsupported operator: {operator}")

        right = tree_node.comparators[0].n
        node = Node("comparison", value=f'{left} {op} {right}')
        return node
    else:
        raise ValueError("Unsupported AST node")

def is_valid_rule(rule_string):
    try:
        tree = ast.parse(rule_string, mode='eval')
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if node.id not in VALID_ATTRIBUTES:
                    return False, f"Invalid attribute: {node.id}"
        return True, ""
    except Exception as e:
        return False, str(e)

def evaluate_rule(rule, data):
    try:
        return eval(rule, {}, data)
    except Exception as e:
        return f"Error: {str(e)}"

def init_db():
    with sqlite3.connect('rules.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS rules
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, rule_string TEXT, created_at TEXT)''')
        conn.commit()

@app.route('/create_rule', methods=['POST'])
def create_rule():
    rule_data = request.get_json()
    rule = rule_data.get('rule')

    is_valid, message = is_valid_rule(rule)
    if not is_valid:
        return jsonify({'message': f"Invalid rule: {message}"}), 400

    with sqlite3.connect('rules.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO rules (rule_string, created_at) VALUES (?, ?)",
                       (rule, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

    return jsonify({'message': 'Rule created successfully!'})

@app.route('/get_rules', methods=['GET'])
def get_rules():
    with sqlite3.connect('rules.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, rule_string FROM rules")
        rules = [{'id': row[0], 'rule_string': row[1]} for row in cursor.fetchall()]
    return jsonify({'rules': rules})

@app.route('/combine_rules', methods=['POST'])
def combine_rules():
    rule_data = request.get_json()
    rule_ids = rule_data.get('rule_ids', [])
    operator = rule_data.get('operator', 'AND')

    if not rule_ids:
        return jsonify({'error': 'No rules selected for combination'}), 400

    with sqlite3.connect('rules.db') as conn:
        cursor = conn.cursor()
        placeholders = ', '.join('?' for _ in rule_ids)
        cursor.execute(f"SELECT rule_string FROM rules WHERE id IN ({placeholders})", rule_ids)
        selected_rules = [row[0] for row in cursor.fetchall()]

    if not selected_rules:
        return jsonify({'error': 'No rules found for the given IDs'}), 400

    combined_rule_string = f" {operator.lower()} ".join(f"({rule})" for rule in selected_rules)

    with sqlite3.connect('rules.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO rules (rule_string, created_at) VALUES (?, ?)",
                       (combined_rule_string, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        combined_rule_id = cursor.lastrowid

    return jsonify({'combined_rule_string': combined_rule_string, 'combined_rule_id': combined_rule_id})

@app.route('/evaluate_rule', methods=['POST'])
def evaluate():
    rule_data = request.get_json()
    rule_id = rule_data.get('rule_id')
    user_data = rule_data.get('data')

    with sqlite3.connect('rules.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rule_string FROM rules WHERE id = ?", (rule_id,))
        result = cursor.fetchone()

        if result:
            rule = result[0]
        else:
            return jsonify({'error': 'Rule not found'}), 404

    result = evaluate_rule(rule, user_data)
    return jsonify({'result': result})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
