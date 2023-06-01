import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *
from jinja2 import Environment, FileSystemLoader
from utils import order

app = Flask(__name__, template_folder='templates')

client = Client(config.API_KEY, config.API_SECRET, tld='us', testnet=config.TESTNET)


@app.route('/')
def welcome():
    return render_template('index.html')

@app.route('/webhook', methods=['GET'])
def webhook():
    data = json.loads(request.data.decode('utf-8'))
    print(data)
    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "Nice try, invalid passphrase"
        }
    order_response = order(client, data)
    return {"Status": order_response}
    
@app.route('/dashboard', methods=['POST','GET'])
def dashboard():
    return render_template('Dashboard.html')

@app.route('/orders_page', methods=['POST','GET'])
def orders_page():
    env = Environment(loader=FileSystemLoader('templates'))
    print(env)
    env.filters['datetimeformat'] = lambda value, format='%Y-%m-%d %H:%M:%S': value.strftime(format)
    template = env.get_template('orders.html')

    # Set up the Binance API endpoint and parameters
    client = Client(config.API_KEY, config.API_SECRET)

    orders = client.get_all_orders(symbol='DOGEUSDT')
    # order_history = json.dumps(list_orders)
    # print(type(order_history))

    # Render the template with the data and write it to a file
    output = template.render({'orders':orders})
    with open('templates/orders_final.html', 'w') as f:
        f.write(output)

    return render_template('orders_final.html')

if __name__ == "__main__":
    app.run()