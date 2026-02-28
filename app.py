import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)
DATABASE = 'pitstop.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # returns dict-like rows
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# intialises the database and creates tables
def init_db():
    """Initializes tables on first run."""
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS Vehicles 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, make TEXT, model TEXT, year INTEGER)''')
        db.execute('''CREATE TABLE IF NOT EXISTS Fuel_Logs 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, date TEXT, 
                      odometer REAL, liters REAL, cost REAL, mileage REAL)''')
        db.commit()

init_db()

#routing
@app.route('/')
def index():
    return render_template('index.html') # The new Hero Page

@app.route('/dashboard')
def dashboard():
    db = get_db()
    logs = db.execute('SELECT * FROM Fuel_Logs ORDER BY date DESC LIMIT 5').fetchall()
    return render_template('dashboard.html', logs=logs)

@app.route('/garage')
def garage():
    db = get_db()
    vehicles = db.execute('SELECT * FROM Vehicles').fetchall()
    return render_template('garage.html', vehicles=vehicles)

@app.route('/add_vehicle', methods=['POST'])
def add_vehicle():
    db = get_db()
    db.execute('INSERT INTO Vehicles (make, model, year) VALUES (?, ?, ?)',
               (request.form['make'], request.form['model'], request.form['year']))
    db.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_fuel', methods=['POST'])
def add_fuel():
    db = get_db()
    v_id = request.form['vehicle_id']
    odo = float(request.form['odometer'])
    liters = float(request.form['liters'])
    cost = float(request.form['cost'])
    
    #calculates mileage 
    last_log = db.execute('SELECT odometer FROM Fuel_Logs WHERE vehicle_id = ? ORDER BY id DESC LIMIT 1', (v_id,)).fetchone()
    mileage = round((odo - last_log['odometer']) / liters, 2) if last_log else 0.0
    
    db.execute('''INSERT INTO Fuel_Logs (vehicle_id, date, odometer, liters, cost, mileage) 
                  VALUES (?, date("now"), ?, ?, ?, ?)''', 
               (v_id, odo, liters, cost, mileage))
    db.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)