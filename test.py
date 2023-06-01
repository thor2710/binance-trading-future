import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *
from jinja2 import Environment, FileSystemLoader
import requests
import time
import datetime

client = Client(config.API_KEY, config.API_SECRET)

# account = client.get_account_snapshot(['SPOT'])

ticker_price = client.get_symbol_ticker(symbol='ETHBTC')['price']

print(ticker_price)


