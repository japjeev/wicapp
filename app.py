from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, SelectField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime


app = Flask(__name__)
app.secret_key='secret123'

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

def get_category(search_term):
        if search_term == 1:
                return "PPTL Cash"
        elif search_term == 2:
                return "PPTL Cheque"
        elif search_term == 3:
                return "PPTL Credit Card"
        elif search_term == 4:
                return "PPTL ACH"
        elif search_term == 5:
                return "Violation/Toll Bill Payments"
        elif search_term == 6:
                return "Account Conversion"
        elif search_term == 7:
                return "Application Processing"
        elif search_term == 8:
                return "Account Closure"
        elif search_term == 9:
                return "Tag Issuance"
        elif search_term == 10:
                return "Account Update (demographics, plans, license plates, etc.)"
                #return "Account Update"
        elif search_term == 11:
                return "Leasing (Uber, Lyft, rentals, etc.)"
        elif search_term == 12:
                return "DMV Suspension (incl. impounded and excluded vehicles)"
        elif search_term == 13:
                return "Other"
        else:
                return "ERROR in function get_category() file app.py"

# get monthly stats data from the DB
def get_monthly_stats():
    ret_str = ""
    c1 = 0.0
    c2 = 0.0
    x = 0.0
    
    # Create cursor
    cur = mysql.connection.cursor()
    query = "SELECT count(*) as 'my_count', \
            CAST(min(unix_timestamp(at_window_ts) - unix_timestamp(entry_ts)) as UNSIGNED INTEGER) as 'my_min', \
            CAST(max(unix_timestamp(at_window_ts) - unix_timestamp(entry_ts)) as UNSIGNED INTEGER) as 'my_max', \
            CAST(avg(unix_timestamp(at_window_ts) - unix_timestamp(entry_ts)) as UNSIGNED INTEGER) as 'my_avg' \
            from wic_visit where MONTH(entry_ts) = MONTH(CURRENT_DATE()) AND YEAR(entry_ts) = \
            YEAR(CURRENT_DATE()) AND at_window_ts is NOT NULL;"
    result = cur.execute(query)
    rows = cur.fetchall()
    if len(rows) > 0:
            for row in rows:
                ret_str = str(row['my_count']) + "," + str(row['my_min']) + "," + str(row['my_max']) + "," + str(row['my_avg'])
                c1 = int(row['my_count'])
    else:
            ret_str = "0,0,0,0"

    query = "select count(*) as 'my_count' from (select abs(unix_timestamp(at_window_ts) - \
            unix_timestamp(entry_ts)) as 'tdiff' from myflaskapp.wic_visit where \
            MONTH(entry_ts) = MONTH(CURRENT_DATE()) AND YEAR(entry_ts) = \
            YEAR(CURRENT_DATE()) and at_window_ts is not null) as table1 where tdiff >= 600;"

    result = cur.execute(query)
    rows = cur.fetchall()
    for row in rows:
        c2 = int(row['my_count'])
    if c1 != 0:
        x = c2/float(c1)
    else:
        x = 0.0
    x = (1-x)*100
    ret_str = ret_str + "," +  str(int(x)) + "%"
    
    cur.close()
    
    return ret_str

# get daily stats data from the DB
def get_daily_stats():
    ret_str = ""
    c1 = 0.0
    c2 = 0.0
    x = 0.0
    d = datetime.now()
    #dstr = datetime.strftime(d, "%Y-%m-%d") + "%"
    dstr = "2017-05-22%"

    # Create cursor
    cur = mysql.connection.cursor()
    result = cur.execute("select count(*) as my_count, \
                CAST(min(unix_timestamp(at_window_ts) - \
                unix_timestamp(entry_ts)) as UNSIGNED INTEGER) \
                as my_min, cast(max(unix_timestamp(at_window_ts) \
                - unix_timestamp(entry_ts)) as UNSIGNED INTEGER) \
                as my_max, cast(avg(unix_timestamp(at_window_ts) \
                - unix_timestamp(entry_ts)) as UNSIGNED INTEGER) \
                as my_avg from wic_visit where entry_ts like %s \
                and at_window_ts is not null", [dstr])
    rows = cur.fetchall()
    if len(rows) > 0:
            for row in rows:
                ret_str = str(row['my_count']) + "," + str(row['my_min']) + "," + str(row['my_max']) + "," + str(row['my_avg'])
                c1 = int(row['my_count'])
    else:
            ret_str = "0,0,0,0"

    result = cur.execute("select count(*) as my_count from (select abs(unix_timestamp(at_window_ts) \
                - unix_timestamp(entry_ts)) as tdiff from myflaskapp.wic_visit where \
                entry_ts like %s and at_window_ts is not null) as table1 where tdiff >= 600", [dstr])
    rows = cur.fetchall()
    for row in rows:
        c2 = int(row['my_count'])
    if c1 != 0:
        x = c2/float(c1)
    else:
        x = 0.0
    x = (1-x)*100
    ret_str = ret_str + "," +  str(int(x)) + "%, " + dstr[:-1]
    
    cur.close()
    
    return ret_str

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Check if admin user logged in
def admin_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            role_type = session['role_type']
            if role_type == 1:
                return f(*args, **kwargs)
            else:
                flash('Unauthorized, Please login as administrator', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Check if admin user logged in
def admin_or_secruity_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            role_type = session['role_type']
            if role_type == 1 or role_type == 3:
                return f(*args, **kwargs)
            else:
                flash('Unauthorized, Please login as administrator', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Check if admin user logged in
def admin_or_csr_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            role_type = session['role_type']
            if role_type == 1 or role_type == 2:
                return f(*args, **kwargs)
            else:
                flash('Unauthorized, Please login as administrator', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Index
@app.route('/')
def index():
    return render_template('home.html')

# About
@app.route('/about')
def about():
    return render_template('about.html')

# Stats
@app.route('/stats')
@admin_logged_in
def stats():
    currentMonth = datetime.now().strftime('%B') + ", " + datetime.now().strftime('%Y') 
    # Create cursor
    cur = mysql.connection.cursor()
    # Get Weekly Stats
    query = "SELECT CONCAT(month(entry_ts), '/', day(entry_ts), '/', year(entry_ts)) as 'day', count(*) as 'my_count', \
        CAST(min(unix_timestamp(at_window_ts) - unix_timestamp(entry_ts)) as UNSIGNED INTEGER) as 'my_min', \
        CAST(max(unix_timestamp(at_window_ts) - unix_timestamp(entry_ts)) as UNSIGNED INTEGER) as 'my_max', \
        CAST(avg(unix_timestamp(at_window_ts) - unix_timestamp(entry_ts)) as UNSIGNED INTEGER) as 'my_avg' \
        FROM wic_visit WHERE YEARWEEK(entry_ts, 1) = YEARWEEK(CURDATE(), 1) AND at_window_ts is NOT \
        NULL GROUP BY day(entry_ts) ORDER BY day(entry_ts) desc;"
    result = cur.execute(query)
    if result > 0:
        weekly_stats = cur.fetchall()
        # Close connection
        cur.close()
    else:
        error = 'No Weekly Stats Found'
        # Close connection
        cur.close()
        return render_template('home.html', error=error)
    return render_template('stats.html', stats_str=get_daily_stats(), stats_str2=get_monthly_stats(), weekly_stats=weekly_stats, currentMonth=currentMonth)

# Users
@app.route('/users')
@admin_logged_in
def users():
    # Create cursor
    cur = mysql.connection.cursor()
    # Get users
    result = cur.execute("SELECT * FROM users;")
    if result > 0:
        users = cur.fetchall()
        # Close connection
        cur.close()
    else:
        error = 'No Visitors Found'
        # Close connection
        cur.close()
        return render_template('home.html', error=error)
    return render_template('users.html', users=users, stats_str=get_daily_stats())

# Delete User
@app.route('/deluser/<string:id>')
@admin_logged_in
def deluser(id):
    # Create cursor
    cur = mysql.connection.cursor()
    # Execute the query
    cur.execute("DELETE FROM users where idusers = %s;", [id])
    # Commit to DB
    mysql.connection.commit()
    # Close connection
    cur.close()
    flash('User Deleted', 'success')
    return redirect(url_for('users'))

# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=3, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Email(message='Invalid email address')])
    password = PasswordField('Password', [
        validators.InputRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')
    role_type = SelectField('Role', choices=[('1', 'Supervisor'), ('2', 'CSR'), ('3', 'Security')]) 


# User Register
@app.route('/register', methods=['GET', 'POST'])
@admin_logged_in
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        role_type = form.role_type.data
        # Create cursor
        cur = mysql.connection.cursor()
        try:
                # Execute query
                cur.execute("INSERT INTO users(name, email, username, password, role_type) VALUES(%s, %s, %s, %s, %s)", (name, email, username, password, role_type))
                # Commit to DB
                mysql.connection.commit()
        except:
                # Close connection
                cur.close()
                error = 'Cannot Add User ' + name
                return render_template('register.html', form=form, error=error)
        
        # Close connection
        cur.close()
        flash('You are now registered and can log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

class UpdateForm(Form):
    name = StringField('Name', [validators.Length(min=3, max=50)])
    email = StringField('Email', [validators.Email(message='Invalid email address')])
    password = PasswordField('Password', [
        validators.InputRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password') 

# User Edit
@app.route('/edituser/<string:id>', methods=['GET', 'POST'])
@admin_logged_in
def edituser(id):

    # Create cursor
    cur = mysql.connection.cursor()
    # Get user by id
    result = cur.execute("SELECT * FROM users WHERE idusers = %s", [id])
    the_user = cur.fetchone()
    cur.close()
    # Get form
    form = UpdateForm(request.form)
    # Populate user form fields
    form.name.data = the_user['name']
    form.email.data = the_user['email']
    
    if request.method == 'POST' and form.validate():
        name = request.form['name']
        email = request.form['email']
        password = sha256_crypt.encrypt(str(request.form['password']))
        # Create cursor
        cur = mysql.connection.cursor()
        try:
                # Execute query
                cur.execute("UPDATE users SET name=%s, email=%s, password=%s WHERE idusers=%s", (name, email, password, id))
                # Commit to DB
                mysql.connection.commit()
        except:
                # Close connection
                cur.close()
                error = 'Cannot Update User ' + name
                return render_template('edituser.html', form=form, error=error)
        
        # Close connection
        cur.close()
        flash('User account updated', 'success')
        return redirect(url_for('users'))
    return render_template('edituser.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']
        # Create cursor
        cur = mysql.connection.cursor()
        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']
            uname = data['name']
            role_type = data['role_type']
            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
                session['uname'] = uname
                session['role_type'] = role_type
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))
    
#Single Visit
@app.route('/single_visit/<string:id>/', methods=['GET', 'POST'])
@admin_or_csr_logged_in
def single_visit(id):
    form = request.form
    if request.method == 'POST':
        checkin_pressed = form["checkin"]
        setcategory_pressed = form["setcategory"]
        category = request.form.getlist('category', type=int)
        checkout_pressed = form["checkout"]
        if checkin_pressed == "Check-In":
            # Create cursor
            cur = mysql.connection.cursor()
            # Execuite the query
            cur.execute("UPDATE wic_visit SET at_window_ts = NOW() where idwic_visit= %s", [id])
            # Commit to DB
            mysql.connection.commit()
            # Close connection
            cur.close()
            flash('Visitor Checked In', 'success')
            return redirect(url_for('single_visit', id=id))
        elif setcategory_pressed == "Select Categories":
            # Create cursor
            cur = mysql.connection.cursor()
            # Execuite the query
            categories = ','.join(str(e) for e in category)
            cur.execute("UPDATE wic_visit SET categories= %s where idwic_visit= %s", [categories, id])
            # Commit to DB
            mysql.connection.commit()
            # Close connection
            cur.close()
            flash('Category Updated', 'success')
            return redirect(url_for('single_visit', id=id))
        elif checkout_pressed == "Check-Out":
            # Create cursor
            cur = mysql.connection.cursor()
            # Execuite the query
            cur.execute("UPDATE wic_visit SET leave_window_ts = NOW() where idwic_visit= %s", [id])
            # Commit to DB
            mysql.connection.commit()
            # Close connection
            cur.close()
            flash('Visitor Checked Out', 'success')
            return redirect(url_for('single_visit', id=id))
        
    # Create cursor
    cur = mysql.connection.cursor()
    # Get visit record
    result = cur.execute("SELECT * FROM wic_visit WHERE idwic_visit = %s", [id])
    if result > 0:
        visit = cur.fetchone()
        str_categories = ""
        my_categories = visit['categories']
        if my_categories == None:
            str_categories = "Pending"
        else:
            my_list = my_categories.split(",")
            for n in range (0,len(my_list)):
                if n == 0:
                    str_categories = get_category(int(my_list[0]))
                else:
                    str_categories = str_categories + ", " + get_category(int(my_list[n]))
        # Close connection
        cur.close()
        return render_template('visit.html', visit=visit, str_categories=str_categories)
    else:
        # Close connection
        cur.close()
        error = 'Visitor not found'
        return render_template('home.html', error=error)       

# Dashboard Form Class
class DashboardForm(Form):
    visitor_id = StringField('Visitor_ID', [validators.InputRequired()])
	
# Dashboard
@app.route('/visitors', methods=['GET', 'POST'])
@is_logged_in
def dashboard():
    form = DashboardForm(request.form)
    if request.method == 'POST' and form.validate():
        visitor_id = form.visitor_id.data        
        # Create cursor
        cur = mysql.connection.cursor()
        # Get visit record from DB
        result = cur.execute("SELECT * FROM wic_visit WHERE idwic_visit = %s", [visitor_id])
        if result > 0:
            visit = cur.fetchone()
            # Close connection
            cur.close()
            return redirect(url_for('single_visit', id=visitor_id))
        else:
            # Create cursor
            cur = mysql.connection.cursor()
            # Get visitors
            result = cur.execute("SELECT * FROM wic_visit ORDER BY entry_ts DESC LIMIT 5;")
            visitors = cur.fetchall()
            # Close connection
            cur.close()
            error = 'Visitor ' + visitor_id + ' not found'
            return render_template('visitors.html', visitors=visitors, form=form, error=error)
    else:       
        # Create cursor
        cur = mysql.connection.cursor()
        # Get visitors
        result = cur.execute("SELECT * FROM wic_visit ORDER BY entry_ts DESC LIMIT 5;")
        visitors = cur.fetchall()
        # Close connection
        cur.close()
        if result > 0:
            return render_template('visitors.html', visitors=visitors, form=form)
        else:
            msg = 'No Visitors Found'
            return render_template('visitors.html', msg=msg, form=form)
        
# New Visitor
@app.route('/new_visitor')
@admin_or_secruity_logged_in
def new_visitor():
    # Create cursor
    cur = mysql.connection.cursor()
    # Execuite the query
    cur.execute("INSERT INTO wic_visit (entry_ts) VALUES (NOW())")
    # Commit to DB
    mysql.connection.commit()
    # Close connection
    cur.close()
    flash('New visitor added', 'success')
    return redirect(url_for('dashboard'))

    
@app.route("/ttwchart")
@admin_logged_in
def ttwchart():
    d = datetime.now()
    #the_date = datetime.strftime(d, "%Y-%m-%d")
    the_date = "2017-05-22"
    cur = mysql.connection.cursor()
    query = "select abs(unix_timestamp(at_window_ts) - unix_timestamp(entry_ts)) as tdiff from wic_visit where entry_ts like '" + the_date + "%';"
    result = cur.execute(query)
    if result > 0:
        wait_times = cur.fetchall()
        return render_template('ttwchart.html',**locals()) 
    else:
        error = 'No Data Found for Wait Time Chart'
        return render_template('home.html', error=error)
    cur.close()

@app.route("/ptchart")
@admin_logged_in
def ptchart():
    d = datetime.now()
    #the_date = datetime.strftime(d, "%Y-%m-%d")
    the_date = "2017-05-22"
    cur = mysql.connection.cursor()
    query = "select abs(unix_timestamp(leave_window_ts) - unix_timestamp(at_window_ts)) as tdiff from wic_visit where entry_ts like '" + the_date + "%';"
    result = cur.execute(query)
    if result > 0:
        service_times = cur.fetchall()
        return render_template('ptchart.html',**locals()) 
    else:
        error = 'No Data Found for Service Time Chart'
        return render_template('home.html', error=error)
    cur.close()

@app.route("/atchart")
@admin_logged_in
def atchart():
    d = datetime.now()
    #the_date = datetime.strftime(d, "%Y-%m-%d")
    the_date = "2017-05-22"
    cur = mysql.connection.cursor()
    query = "select hour(entry_ts) as my_hour, count(*) as my_count \
        from wic_visit where entry_ts like '" + the_date + "%' \
        group by hour(entry_ts), day(entry_ts) order by \
        day(entry_ts), hour(entry_ts);"
    result = cur.execute(query)
    if result > 0:
        activity_timeline = cur.fetchall()
        return render_template('atchart.html',**locals()) 
    else:
        error = 'No Data Found for Activity Timeline Chart'
        return render_template('home.html', error=error)
    cur.close()

@app.route("/scdchart")
@admin_logged_in
def scdchart():
    d = datetime.now()
    #the_date = datetime.strftime(d, "%Y-%m-%d")
    the_date = "2017-05-22"
    cur = mysql.connection.cursor()
    query = "select categories, count(*) as my_count from wic_visit \
        where entry_ts like '" + the_date + "%' group by categories;"
    result = cur.execute(query)
    if result > 0:
        scd_list = cur.fetchall()
        for j in scd_list:
            j["categories"] =  get_category(int(j["categories"]))
        return render_template('scdchart.html',**locals()) 
    else:
        error = 'No Data Found for Service Category Distribution Chart'
        return render_template('home.html', error=error)
    cur.close()

if __name__ == '__main__':
    app.run(debug=True)
