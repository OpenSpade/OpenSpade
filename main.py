from openspade.api.app import app

def main():
    app.run(debug=False, host='0.0.0.0', port=5000)


if __name__ == "__main__":
    main()
