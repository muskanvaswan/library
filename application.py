from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, day

# Configure application
app = Flask(__name__)

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///library.db")


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect(url_for("index"))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password and confirmation match
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        # hash the password and insert a new user in the database
        hash = generate_password_hash(request.form.get("password"))
        new_user_id = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
                                 username=request.form.get("username"),
                                 hash=hash)

        # unique username constraint violated?
        if not new_user_id:
            return apology("username taken", 400)

        # Remember which user has logged in
        session["user_id"] = new_user_id

        # Display a flash message
        flash("Registered!")

        # Redirect user to home page
        return redirect(url_for("index"))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/add_b", methods=["GET", "POST"])
@login_required
def add_b():

    if request.method == "POST":
        # ensure name is entered
        if not request.form.get("name"):
            return apology("name must be entered",400)

        # add book to database
        db.execute("INSERT INTO books(user_id, name) VALUES(:user_id, :name)",user_id=session["user_id"],
                   name=request.form.get("name"))
        id = db.execute("SELECT id FROM books WHERE name=:name",name=request.form.get("name"))

        flash("Book Added!")

        # Redirect user to home page
        return redirect(url_for("index"))

    else:
        return render_template("add_b.html")

@app.route("/add_m", methods=["GET", "POST"])
@login_required
def add_m():

    if request.method == "POST":
        # ensure name is entered
        if not request.form.get("name"):
            return apology("name must be entered",400)

        # add book to database
        db.execute("INSERT INTO members(user_id, name) VALUES(:user_id, :name)",user_id=session["user_id"],
                   name=request.form.get("name"))

        id = db.execute("SELECT id FROM books WHERE name=:name",name=request.form.get("name"))

        flash("Member added")


        # Redirect user to home page
        return redirect(url_for("index"))

    else:
        return render_template("add_m.html")

@app.route("/rec_b")
@login_required
def rec_b():
    books = db.execute("SELECT * FROM books WHERE user_id=:user",user=session["user_id"])
    return render_template("dis_b.html",records=books)


@app.route("/rec_m")
@login_required
def rec_m():
    members = db.execute("SELECT * FROM members WHERE user_id=:user",user=session["user_id"])
    return render_template("dis_m.html",records=members)

@app.route("/rec_i")
@login_required
def rec_i():
    issued = db.execute("SELECT * FROM issue WHERE user_id=:user",user=session["user_id"])
    return render_template("dis_i.html", issues=issued)


@app.route("/issue", methods=["GET","POST"])
@login_required
def issue():
    if request.method == "POST":

        if not request.form.get("member_id"):
            return apology("Member ID must be entered",400)

        if not request.form.get("book_id"):
            return apology("Book ID must be entered",400)

        member = db.execute("SELECT *FROM members WHERE (id=:mid AND user_id=:user)",mid=request.form.get("member_id"),user=session["user_id"])
        if not member:
            return apology("Member ID invalid",400)

        book = db.execute("SELECT *FROM books WHERE (id=:bid AND user_id=:user)",bid=request.form.get("book_id"),user=session["user_id"])
        if not book:
            return apology("Book ID invalid",400)

        db.execute("INSERT INTO issue(member_id,book_id,user_id,member_n,book_n) VALUES (:mid,:bid,:user,:mn,:bn)",
                        mid=request.form.get("member_id"), bid=request.form.get("book_id"),user=session["user_id"],
                        mn=member[0]["name"],bn= book[0]["name"])

        db.execute("UPDATE books SET status='issued' WHERE id=:bid",bid=request.form.get("book_id"))

        flash("Book has been Issued!")

        return redirect(url_for("index"))

    else:
        return render_template("issue.html")

@app.route("/returned",methods=["GET","POST"])
@login_required
def returned():
    if request.method == "POST":

        fine = 0.00

        if not request.form.get("member_id"):
            return apology("Member ID must be entered",400)

        if not request.form.get("book_id"):
            return apology("Book ID must be entered",400)


        issue = db.execute("SELECT *FROM issue WHERE (book_id=:bid AND user_id=:user AND member_id=:mid)",
                                    bid=request.form.get("book_id"),user=session["user_id"],mid=request.form.get("member_id"))
        if not issue:
            return apology("Not Issued",400)

        date = db.execute("SELECT date FROM issue WHERE (book_id=:bid AND user_id=:user)",
                            bid=request.form.get("book_id"),user=session["user_id"])
        date1 = date[0]['date']
        if day(date1)>7:
            for i in range(day(date)-7):
                fine+=1


        db.execute("DELETE FROM issue WHERE (book_id=:bid AND user_id=:user)",bid=request.form.get("book_id"),user=session["user_id"])

        db.execute("UPDATE books SET status='available' WHERE id=:bid",bid=request.form.get("book_id"))

        if fine!=0:
            return render_template("returned.html",fine=fine)

        else:
            flash("Book has been returned!")
            return redirect(url_for("index"))

    else:
        return render_template("return.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

