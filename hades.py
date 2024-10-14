import tkinter as tk
from tkinter import ttk, simpledialog
import requests
import json
import os
import webbrowser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from PIL import Image, ImageTk  # For loading the PNG icon

# File to save and load cryptocurrency list
CRYPTO_FILE = "cryptos.json"

# Load cryptocurrencies from JSON file
def load_cryptos():
    if os.path.exists(CRYPTO_FILE):
        with open(CRYPTO_FILE, "r") as f:
            return json.load(f)
    else:
        # Default cryptocurrencies if no file exists
        return ["bitcoin", "ethereum", "dogecoin", "monero", "tron"]

# Save cryptocurrencies to JSON file
def save_cryptos(cryptos):
    with open(CRYPTO_FILE, "w") as f:
        json.dump(cryptos, f)

# Fetch cryptocurrency data (INR and USD prices)
def get_crypto_data(cryptos):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params_inr = {
        "vs_currency": "inr",  # INR base currency
        "ids": ','.join(cryptos)  # List of cryptocurrencies to fetch
    }
    params_usd = {
        "vs_currency": "usd",  # USD base currency
        "ids": ','.join(cryptos)
    }
    try:
        response_inr = requests.get(url, params=params_inr)
        response_inr.raise_for_status()  # Raise exception for bad response
        data_inr = response_inr.json()

        response_usd = requests.get(url, params=params_usd)
        response_usd.raise_for_status()  # Raise exception for bad response
        data_usd = response_usd.json()

        return data_inr, data_usd
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return [], []

# Update the GUI with crypto data
def update_gui():
    crypto_names = [crypto.get() for crypto in crypto_vars]
    data_inr, data_usd = get_crypto_data(crypto_names)

    for idx, (crypto_inr, crypto_usd) in enumerate(zip(data_inr, data_usd)):
        try:
            current_price_inr = f"₹{crypto_inr['current_price']}"
            current_price_usd = f"${crypto_usd['current_price']}"
            price_change = crypto_inr.get("price_change_percentage_24h", 0)
            color = "green" if price_change > 0 else "red"

            # Update labels for crypto prices and changes
            name_labels[idx].config(text=crypto_inr["name"].capitalize())
            price_inr_labels[idx].config(text=current_price_inr)
            price_usd_labels[idx].config(text=current_price_usd)
            change_labels[idx].config(text=f"{price_change:.2f}%")
            change_labels[idx].config(fg=color)

            # Bind the click event to open a detailed webpage on the coin
            change_labels[idx].bind("<Button-1>", lambda e, crypto=crypto_inr["id"]: open_browser(crypto))
        except (TypeError, KeyError) as e:
            print(f"Error processing data for {crypto_names[idx]}: {e}")
            name_labels[idx].config(text=crypto_names[idx].capitalize())
            price_inr_labels[idx].config(text="N/A")
            price_usd_labels[idx].config(text="N/A")
            change_labels[idx].config(text="N/A", fg="black")

    root.after(10000, update_gui)

# Function to open the web browser for the clicked crypto
def open_browser(crypto):
    url = f"https://www.coingecko.com/en/coins/{crypto}"
    webbrowser.open_new(url)

# Display historical price graph
def show_graph(crypto):
    url = f"https://api.coingecko.com/api/v3/coins/{crypto}/market_chart"
    params = {
        "vs_currency": "inr",
        "days": "30"  # Fetch data for the last 30 days
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for bad response
        response_data = response.json()

        if "prices" not in response_data:
            print(f"Unexpected response format for {crypto}.")
            return

        dates = [datetime.utcfromtimestamp(point[0] // 1000) for point in response_data["prices"]]
        prices = [point[1] for point in response_data["prices"]]

        # Plot the graph
        fig, ax = plt.subplots()
        ax.plot(dates, prices, marker="o", color="blue")
        ax.set_title(f"{crypto.capitalize()} Price Trend (INR)")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price (INR)")
        ax.grid(True)

        # Display the graph in a new Tkinter window
        graph_window = tk.Toplevel(root)
        graph_window.title(f"{crypto.capitalize()} Price Chart")

        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching or displaying graph for {crypto}: {e}")
    except KeyError as e:
        print(f"Missing data in response: {e}")

# Add new cryptocurrency to the list
def add_crypto():
    new_crypto = simpledialog.askstring("Add Cryptocurrency", "Enter the cryptocurrency name (e.g., litecoin):")
    if new_crypto:
        crypto_vars.append(tk.StringVar(value=new_crypto))
        create_crypto_row(len(crypto_vars) - 1)
        save_cryptos([crypto.get() for crypto in crypto_vars])
        update_gui()

# Create a new row for displaying cryptocurrency data
def create_crypto_row(index):
    name_label = tk.Label(frame, text="", font=("Arial", 10))
    price_inr_label = tk.Label(frame, text="", font=("Arial", 10))
    price_usd_label = tk.Label(frame, text="", font=("Arial", 10))
    change_label = tk.Label(frame, text="", font=("Arial", 10))

    name_label.grid(row=index+1, column=0, padx=10, pady=5)
    price_inr_label.grid(row=index+1, column=1, padx=10, pady=5)
    price_usd_label.grid(row=index+1, column=2, padx=10, pady=5)
    change_label.grid(row=index+1, column=3, padx=10, pady=5)


    name_label.bind("<Button-1>", lambda e, crypto=crypto_vars[index].get(): show_graph(crypto))

    name_labels.append(name_label)
    price_inr_labels.append(price_inr_label)
    price_usd_labels.append(price_usd_label)
    change_labels.append(change_label)

# Setup the main Tkinter window
root = tk.Tk()
root.title("Cryptocurrency Value Indicator")

# Set the window icon using conky.png
icon_path = "crypto.png"
if os.path.exists(icon_path):
    img = Image.open(icon_path)
    icon = ImageTk.PhotoImage(img)
    root.iconphoto(False, icon)

# Create a frame to hold the crypto data
frame = ttk.Frame(root)
frame.pack(padx=10, pady=10)

# Create headers for the grid
header_name = tk.Label(frame, text="Cryptocurrency", font=("Arial", 12, "bold"))
header_price_inr = tk.Label(frame, text="Price (INR)", font=("Arial", 12, "bold"))
header_price_usd = tk.Label(frame, text="Price (USD)", font=("Arial", 12, "bold"))
header_change = tk.Label(frame, text="24h Change", font=("Arial", 12, "bold"))

header_name.grid(row=0, column=0, padx=10, pady=5)
header_price_inr.grid(row=0, column=1, padx=10, pady=5)
header_price_usd.grid(row=0, column=2, padx=10, pady=5)
header_change.grid(row=0, column=3, padx=10, pady=5)

# Load cryptocurrencies from the JSON file
crypto_names = load_cryptos()

# Lists to store the labels for dynamic updates
crypto_vars = [tk.StringVar(value=crypto) for crypto in crypto_names]
name_labels = []
price_inr_labels = []
price_usd_labels = []
change_labels = []

# Create rows for each cryptocurrency
for i in range(len(crypto_vars)):
    create_crypto_row(i)

# Button to add new cryptocurrency
add_crypto_button = tk.Button(root, text="Add Cryptocurrency", command=add_crypto)
add_crypto_button.pack(pady=10)

# Start updating the data in the GUI
update_gui()

root.mainloop()
