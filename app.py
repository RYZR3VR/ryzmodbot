from flask import Flask, request

app = Flask(__name__)

@app.route("/discord-webhook", methods=["POST", "GET"])
def webhook():
    return "Webhook active", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
