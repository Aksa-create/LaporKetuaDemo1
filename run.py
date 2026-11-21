from app import create_app

app = create_app()

if __name__ == "__main__":
    print("\n====================================")
    print("       LAPORKETUA - SERVER")
    print("====================================")
    print("Login Umum : http://127.0.0.1:5000/masuk")
    print("Login Admin: http://127.0.0.1:5000/admin/masuk")
    print("====================================\n")

    app.run(debug=True)