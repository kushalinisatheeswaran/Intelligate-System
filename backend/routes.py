from flask import Flask, request, jsonify
from database import get_connection

app = Flask(__name__)

@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.json
    identifier = data.get("identifier")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE identifier = %s", (identifier,))
    user = cur.fetchone()

    if user:
        status = "GRANTED"
    else:
        status = "DENIED"

    cur.execute(
        "INSERT INTO logs (identifier, status, method) VALUES (%s, %s, %s)",
        (identifier, status, "ANPR/Barcode")
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": status})