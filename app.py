from flask import Flask, render_template, request, redirect

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/post", methods=['POST'])
def getPost():
    a = request.form
    print("get!!!    ", a)
    return redirect("/")


if __name__ == '__main__':
    app.run()
