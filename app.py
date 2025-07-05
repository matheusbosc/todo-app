from cs50 import SQL

from flask import Flask, redirect, render_template, request, session
from flask_session import Session

from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, login_not_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///todo.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    '''Manage the todo list'''
    table = f"{session['user_id']}todo"

    if request.method == "POST":
        
        action = request.form.get("action")
        
        if action == "add":
            title = request.form.get("t")
            desc = request.form.get("d")

            if not title:
                return apology("Title must not be empty!", 400)
            elif not desc:
                return apology("Description must not be empty!", 400)

            try:
                db.execute(f"INSERT INTO `{table}` (title, description) VALUES (?, ?);", title, desc)
            except Exception as e:
                print("Error inserting item:", e)
                return apology("Unable to add data to the database!", 500)

            return redirect("/")
        
        elif action == "delete":
            if not request.form.get("id"):
                return apology("ID must not be empty!", 400) # IS ID EMPTY
            
            try:
                db.execute("DELETE FROM ? WHERE `item-id`=?;", f"{session["user_id"]}todo", request.form.get("id")) # DELETE ITEM
            except Exception as e:
                print("Error deleting item:", e)
                return apology("Unable to add data to the database!", 500)
            
            return redirect("/")
        
        elif action == "check":
            if not request.form.get("id"):
                return apology("ID must not be empty!", 400) # IS ID EMPTY
            
            if not request.form.get("checked"): # NOT CHECKED
                try:
                    db.execute("UPDATE ? SET checked=0 WHERE `item-id`=?;", f"{session["user_id"]}todo", request.form.get("id")) # UPDATE ITEM
                except Exception as e:
                    print("Error updating item:", e)
                    return apology("Unable to modify data on the database!", 500)
                
            elif request.form.get("checked") == "on":
                try:
                    db.execute("UPDATE ? SET checked=1 WHERE `item-id`=?;", f"{session["user_id"]}todo", request.form.get("id")) # UPDATE ITEM
                except Exception as e:
                    print("Error updating item:", e)
                    return apology("Unable to modify data on the database!", 500)
            
            return redirect("/")
        
        return apology("Unknown action", 400)
    
    else:
        return render_template("index.html", items=db.execute("SELECT * FROM ? ORDER BY `item-id` DESC", f"{session["user_id"]}todo"))
    
@app.route("/shared", methods=["GET", "POST"])
@app.route("/shared/", methods=["GET", "POST"])
@login_required
def shared():
    
    if request.method == "POST":
        if request.form.get("action") == "lose":
            #Lose Access
            try:
                db.execute("DELETE FROM `shared-access` WHERE `owner-id` IN (SELECT id FROM users WHERE username=?)", request.form.get("u"))
            except Exception as e:
                print(e)
                return apology("Unable to remove from the database!", 500)
            
            
            return redirect("/shared")
        else:
            return apology("Unknown Error", 500)
    else:
        try:
            usernames = db.execute("SELECT username FROM users WHERE id IN (SELECT `owner-id` FROM `shared-access` WHERE `viewer-id`=?)", session["user_id"])
        except Exception as e:
            print(e)
            return apology("Unable to get data from the database!", 500)
        
        print(usernames)
    
        return render_template("shared.html", usernames=usernames)

@app.route('/shared/<username>', methods=['GET', 'POST'])
@login_required
def shared_page(username): # Open a list shared with you
    
    
    # CHECK IF YOU HAVE ACCESS
    if not username:
            return redirect("/shared")
    
    try:
        user_id = db.execute("SELECT id FROM users WHERE username = ?", username)
    except Exception as e:
        print(e)
        return apology("Unable to check access. Try again later!", 500)
    
    if user_id:
        user_id = user_id[0]["id"]
    else:
        return apology("User not found!", 404)
    
    try:
        users = db.execute("SELECT `owner-id` FROM `shared-access` WHERE `viewer-id`=?", session["user_id"])
    except Exception as e:
        print(e)
        return apology("Unable to check access. Try again later!", 500)

    for user in users:
        if user["owner-id"] == user_id:
            break
    else:
        return apology("You do not have access to view this list!", 403)
    
    # CHECK ACTION
    table = f"{user_id}todo"

    if request.method == "POST":
        
        action = request.form.get("action")
        
        if action == "add":
            title = request.form.get("t")
            desc = request.form.get("d")

            if not title:
                return apology("Title must not be empty!", 400)
            elif not desc:
                return apology("Description must not be empty!", 400)

            try:
                db.execute(f"INSERT INTO `{table}` (title, description) VALUES (?, ?);", title, desc)
            except Exception as e:
                print("Error inserting item:", e)
                return apology("Unable to add data to the database!", 500)

            return redirect(f"/shared/{username}")
        
        elif action == "delete":
            if not request.form.get("id"):
                return apology("ID must not be empty!", 400) # IS ID EMPTY
            
            try:
                db.execute("DELETE FROM ? WHERE `item-id`=?;", f"{user_id}todo", request.form.get("id")) # DELETE ITEM
            except Exception as e:
                print("Error deleting item:", e)
                return apology("Unable to add data to the database!", 500)
            
            return redirect(f"/shared/{username}")
        
        elif action == "check":
            if not request.form.get("id"):
                return apology("ID must not be empty!", 400) # IS ID EMPTY
            
            if not request.form.get("checked"): # NOT CHECKED
                try:
                    db.execute("UPDATE ? SET checked=0 WHERE `item-id`=?;", f"{user_id}todo", request.form.get("id")) # UPDATE ITEM
                except Exception as e:
                    print("Error updating item:", e)
                    return apology("Unable to modify data on the database!", 500)
                
            elif request.form.get("checked") == "on":
                try:
                    db.execute("UPDATE ? SET checked=1 WHERE `item-id`=?;", f"{user_id}todo", request.form.get("id")) # UPDATE ITEM
                except Exception as e:
                    print("Error updating item:", e)
                    return apology("Unable to modify data on the database!", 500)
            
            return redirect(f"/shared/{username}")
        
        return apology("Unknown action", 400)
    
    else:

        return render_template("index-shared.html", items=db.execute("SELECT * FROM ? ORDER BY `item-id` DESC", f"{user_id}todo"), path=f"/shared/{username}", name=username)

@app.route("/login", methods=["GET", "POST"])
@login_not_required
def login():
    '''Log User into the web app'''
    
    if request.method == "POST":
        
        if not request.form.get("u"):
            return apology("Username must not be empty!", 400) # IS USERNAME EMPTY
        elif not request.form.get("p"):
            return apology("Password must not be empty!", 400) # IS PASSWORD EMPTY
        
        session["user_id"] = None # CLEAR SESSION
        
        users = None
        
        try:
            users = db.execute("SELECT * FROM users WHERE username = ?;", request.form.get("u")) # GET ALL USERS WITH THAT USERNAME
        except Exception as e:
            return apology("Unable to get data from the database!", 500)
        else:
            if not users:
                return apology("Username or password is invalid!", 401) # IS USER INVALID
        
        if check_password_hash(users[0]["password"], request.form.get("p")):
            session["user_id"] = users[0]["id"]
            print(session["user_id"])
        else:
            return apology("Username or password is invalid!", 401) # IS PASSWORD INVALID
        
        return redirect("/")
    
    else:
        return render_template("login.html")
    
@app.route("/share", methods=["GET", "POST"])
@login_required
def share():
    
    if request.method == "POST":
        
        if not request.form.get("u"):
            return apology("Username must not be empty", 400)
        
        if request.form.get("action") == "add":
            
            try:
                db.execute("INSERT INTO `shared-access` VALUES (?, (SELECT id FROM users WHERE username = ?))", session["user_id"], request.form.get("u"))
            except Exception as e:
                print(e)
                return apology("Unable to add user to the database!", 500)
            
            return redirect("/share")
        elif request.form.get("action") == "del":
            
            try:
                db.execute("DELETE FROM `shared-access` WHERE `owner-id` = ? AND `viewer-id` = (SELECT id FROM users WHERE username = ?)", session["user_id"], request.form.get("u"))
            except Exception as e:
                print(e)
                return apology("Unable to delete user from the database!", 500)
            
            return redirect("/share")
        else:
            return apology("Unknown Action", 400)
    
    else:
        
        try:
            usernames = db.execute("SELECT username FROM users WHERE id IN (SELECT `viewer-id` FROM `shared-access` WHERE `owner-id` = ?)", session["user_id"])
        except Exception as e:
            print(e)
            return apology("Unable to get list of users from the database!", 500)
        
        return render_template("share.html", usernames=usernames)

@app.route("/register", methods=["GET", "POST"])
@login_not_required
def register():
    '''Register User into the web app'''

    if request.method == "POST":
        
        if not request.form.get("u"):
            return apology("Username must not be empty!", 400) # IS USERNAME EMPTY
        elif not request.form.get("p"):
            return apology("Password must not be empty!", 400) # IS PASSWORD EMPTY
        elif not request.form.get("pc"):
            return apology("Password Confirmation must not be empty!", 400) # IS CONFIRMATION EMPTY
        elif request.form.get("p") != request.form.get("pc"):
            return apology("Passwords must match!", 400) # DO PASSWORDS MATCH
    
        session["user_id"] = None # RESET SESSION
    
        db.execute("BEGIN") # START SQL QUERIES
    
        try:
            db.execute("INSERT INTO users (`username`, `password`) VALUES (?, ?)", request.form.get("u"), generate_password_hash(request.form.get("p"))) # INSERTS USER INFO INTO DB
            t = db.execute("SELECT id FROM users WHERE username = ?", request.form.get("u")) # GETS THE USER ID
            print(t)
            db.execute('CREATE TABLE ? (`item-id` INTEGER PRIMARY KEY AUTOINCREMENT, `title` TEXT, `description` TEXT, `checked` INTEGER DEFAULT 0)', f"{t[0]["id"]}todo") # CREATES A TABLE FOR USER
        except Exception as e:
            db.execute("ROLLBACK") # CANCEL QUERIES IF FAILED
            return apology("Unable to register due to server error!", 500)
        else:
            db.execute("COMMIT") # SUBMIT QUERIES IF SUCCEEDED
    
        return redirect("/login")

    else:
        return render_template("register.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    '''Manage User Profile'''
    
    if request.method == "POST":
        
        if request.form.get("action") == "change":
            
            return redirect("/change-password")
        
        elif request.form.get("action") == "clear":
            
            try:
                db.execute("DELETE FROM ?", f"{session["user_id"]}todo")
            except Exception as e:
                print(e)
                return apology("Unable to clear due to server error!", 500)
            
            return redirect("/")
        
        elif request.form.get("action") == "delete":
            
            db.execute("BEGIN")
            try:
                db.execute("DROP TABLE ?", f"{session["user_id"]}todo")
                db.execute("DELETE FROM `shared-access` WHERE `owner-id` = ?", session["user_id"])
                db.execute("DELETE FROM `shared-access` WHERE `viewer-id` = ?", session["user_id"])
                db.execute("DELETE FROM users WHERE id=?", session["user_id"])
            except Exception as e:
                print(e)
                db.execute("ROLLBACK") # CANCEL QUERIES IF FAILED
                return apology("Unable to delete due to server error!", 500)
            else:
                db.execute("COMMIT") # COMMIT QUERIES IF SUCCEEDED
            
            session["user_id"] = None # CLEAR SESSION
            
            return redirect("/login")

    else:
        t = db.execute("SELECT username FROM users WHERE id=?", session["user_id"])
        name = t[0]["username"]
        
        return render_template("profile.html", name=name)

@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    '''Change User Password'''
    
    if request.method == "POST":
        
        if not request.form.get("p"):
            return apology("Password must not be empty!", 400) # IS PASSWORD EMPTY
        elif not request.form.get("pc"):
            return apology("Password Confirmation must not be empty!", 400) # IS CONFIRMATION EMPTY
        elif request.form.get("p") != request.form.get("pc"):
            return apology("Passwords must match!", 400) # DO PASSWORDS MATCH
    
        db.execute("BEGIN")
    
        try:
            db.execute("UPDATE users SET password = ? WHERE id = ?", generate_password_hash(request.form.get("p")), session["user_id"])
        except Exception as e:
            db.execute("ROLLBACK") # CANCEL QUERIES IF FAILED
            return apology("Unable to change due to server error!", 500)
        else:
            db.execute("COMMIT") # COMMIT QUERIES IF SUCCEEDED
    
        session["user_id"] = None
    
        return redirect("/login")
    
    else:
        return render_template("change_password.html")

@app.route("/logout")
@login_required
def logout():
    '''Logout'''
    
    session["user_id"] = None
    
    return redirect("/")