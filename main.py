from flask import Flask,render_template,request,jsonify,session,url_for,send_file,redirect,make_response
import pandas as pd
import os,mysql.connector,io
from werkzeug.security import generate_password_hash, check_password_hash 
from functools import wraps
from datetime import datetime 
from dotenv import load_dotenv
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf


app=Flask(__name__)

load_dotenv()

app.secret_key = os.getenv("SECRET_KEY")

# CSRF Protection
csrf = CSRFProtect(app)

@app.template_global()
def csrf_token():
    return generate_csrf()

app.config.update(
    SESSION_COOKIE_SECURE=True, # Prevents client-side JavaScript from accessing session cookies.
    SESSION_COOKIE_HTTPONLY=True, #Only sends cookies over HTTPS
    SESSION_COOKIE_SAMESITE='Lax' #Prevents CSRF in most cases by disallowing cookies in cross-site POST requests.
)


def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    return connection

#One-time Initialization for NEXTUP table 
def insert_nextup():
    app_username = 'admin'  # system user
    try:
        conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM NEXTUP WHERE TYPE = %s", ('ASN',))
        count = cursor.fetchone()[0]
        if count > 0:
            print(" 'ASN' record already exists in NEXTUP. Skipping insert.")
            return
        sql = """
            INSERT INTO NEXTUP (
                TYPE, STARTINGNUMBER, ENDINGNUMBER, CURRENTNUMBER,
                NEXTNUMBER, ADDDATE, USERCREATED, DATEUPDATED, USERUPDATED,PREFIX
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        now = datetime.now()
        values = (
            'ASN', 'ASN10000001', 'ASN99999999', 'ASN10000001',
            'ASN10000002', now, app_username, now, app_username,'ASN'
        )
        cursor.execute(sql, values)
        print("About to commit...")
        conn.commit()
        print(" NEXTUP table initialized with ASN sequence.")
    except mysql.connector.Error as err:
        print(" MySQL Error during NEXTUP insert:", err)
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


# --- Auth helpers ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Registration ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)
        ADDDATE = datetime.now()
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO USERMASTER (USERNAME, PASSWORD, ADDDATE) VALUES (%s, %s, %s)",
                (username, hashed_pw, ADDDATE)
            )
            conn.commit()
            return redirect(url_for('login'))
        except mysql.connector.Error:
            return render_template('register.html', error="Username already exists.")
        finally:
            cursor.close()
            conn.close()
    return render_template('register.html')

# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT * FROM USERMASTER WHERE USERNAME=%s", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user['PASSWORD'], password):
                last_login_time = datetime.now()
                cursor.execute("""
                    UPDATE USERMASTER 
                    SET LASTLOGIN = %s 
                    WHERE ID = %s
                """, (last_login_time, user['ID']))
                conn.commit()

                session['user_id'] = user['ID']
                session['username'] = user['USERNAME']

                return redirect(url_for('mainpage'))
            else:
                return render_template('login.html', error="Invalid credentials.")
        
        except mysql.connector.Error as e:
            print("Login DB Error:", e)
            return render_template('login.html', error="Database error.")
        
        finally:
            cursor.close()
            conn.close()

    return render_template('login.html')


# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def mainpage():
    return render_template('main.html')


@app.route('/firstpage')
@login_required
def firstpage():
    return render_template('index.html')

@app.route('/capture_owner',methods=['POST'])
@login_required
def capture_owner():
    data=request.get_json()
    owner=data.get('owner')
    print(f"Owner: {owner}")
    
    session['owner']=owner
    
    return jsonify({'redirect': url_for('second_html')})

@app.route('/inventory')
@login_required
def second_html():
    return render_template('inventory.html')

@app.route('/second_form', methods=['POST'])
@login_required
def capture_inventory():
    data = request.get_json()
    locn = data.get('locn')
    sku = data.get('sku')
    LPN = data.get('LPN')
    uom = data.get('uom')
    qty = data.get('qty')
    owner = session.get('owner')
    username = session.get('username')
    ADDDATE = datetime.now()

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Insert into INVENTORYCAPTURE table first
        sql = """INSERT INTO INVENTORYCAPTURE 
                (OWNER, LOCATION, SKU, LPN, UOM, QTY, USERNAME, ADDDATE) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        val = (owner, locn, sku, LPN, uom, qty, username, ADDDATE)
        cursor.execute(sql, val)
        conn.commit()
        
        return jsonify({"message": "Inventory data saved successfully!"}), 200

    except mysql.connector.Error as err:
        print("MySQL Error:", err)
        if conn:
            conn.rollback()
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        print("General Error:", e)
        if conn:
            conn.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            
@app.route('/download_excel')
@login_required
def download_excel():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        username = session.get('username')

        #  Fetch all unprocessed inventory records
        cursor.execute("""
            SELECT * FROM INVENTORYCAPTURE 
            WHERE STATUS IS NULL OR STATUS = ''
            ORDER BY ADDDATE 
        """)
        pending_inventory = cursor.fetchall()

        if not pending_inventory:
            return jsonify({"error": "No new inventory data to assign ASN/line."}), 404

        # Loop and assign ASN/Line, insert into download_table
        for record in pending_inventory:
            owner = record['OWNER']
            locn = record['LOCATION']
            sku = record['SKU']
            lpn = record['LPN']
            uom = record['UOM']
            qty = record['QTY']
            
            
            ADDDATE = datetime.now()

            # Call the stored procedure
            cursor.execute("""
                CALL GenerateASNLineNumber(%s, %s, @asn_out, @line_out, @status_out, @msg_out)
            """, (owner, username))
            cursor.execute("""
                SELECT @asn_out AS ASNNUMBER, @line_out AS LINENUMBER, 
                       @status_out AS status, @msg_out AS message
            """)
            proc_result = cursor.fetchone()

            if proc_result['status'] != 'SUCCESS':
                print(f"[ERROR] ASN generation failed for SKU: {sku}, Reason: {proc_result['message']}")
                continue  # Skip this record and move to next

            ASNNUMBER = proc_result['ASNNUMBER']
            LINENUMBER = proc_result['LINENUMBER']

            # Insert into download_table
            cursor.execute("""
                INSERT INTO DOWNLOADTABLE 
                (OWNER,ASNNUMBER,LINENUMBER,LOCATION,SKU,LPN,UOM, QTY, USERNAME,ADDDATE)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (owner,ASNNUMBER,LINENUMBER,locn, sku,lpn, uom, qty, username, ADDDATE))

            # Mark INVENTORYCAPTURE record as processed
            cursor.execute("""
                UPDATE INVENTORYCAPTURE SET STATUS = 'Y' WHERE ID = %s
            """, (record['ID'],))

        conn.commit()

        df1 = pd.read_sql(
            '''SELECT DISTINCT "" as `Column Name`, "" as `GenericKey`, 
                      ASNNUMBER as `ASN/Receipt`, OWNER as `Owner`, STATUS as `Receipt Status` 
               FROM DOWNLOADTABLE WHERE DOWNLOADSTATUS = 'No' ''',
            conn
        )

        df2 = pd.read_sql(
            '''SELECT "" as `Column Name`, "" as `GenericKey`, ASNNUMBER as `ASN/Receipt`, 
                      SKU as `Item`, OWNER as `Owner`, LINENUMBER as `Line #`, QTY as `Expected Qty`, 
                      UOM as `UOM`, LPN as `LPN`, LOCATION as `LOCATION` 
               FROM DOWNLOADTABLE WHERE DOWNLOADSTATUS = 'No' ''',
            conn
        )
        
        if df1.empty or df2.empty:
            return jsonify({"error": "No data available to export"}), 404

        cursor = conn.cursor()
        cursor.execute("UPDATE DOWNLOADTABLE SET DOWNLOADSTATUS = 'YES' WHERE DOWNLOADSTATUS = 'No'")
        conn.commit()
        cursor.close()

    except Exception as e:
        print("Error in download_excel:", e)
        return jsonify({"error": "Database error while exporting"}), 500

    finally:
        conn.close()
    
    #first sheet details
    header_row_first_sheet=["Column Name", "GenericKey", "RECEIPTKEY","STOREKEY","Status"]
    
    first_row=["Messages", "GenericKey"] + list(df1.columns[2:])
    
    df1.columns = header_row_first_sheet
 
    final_df1 = pd.DataFrame([first_row], columns=header_row_first_sheet)
    final_df1 = pd.concat([final_df1, df1], ignore_index=True)
    
    #second sheet details   
    header_row_1 = [
        "Column Name", "GenericKey", "RECEIPTKEY", "SKU","STOREKEY", "RECEIPTLINENUMBER", "QTYEXPECTED", "UOM", "TOID", "TOLOC"]
    
    second_row = ["Messages", "GenericKey"] + list(df2.columns[2:])

    df2.columns = header_row_1

    final_df2 = pd.DataFrame([second_row], columns=header_row_1)
    final_df2 = pd.concat([final_df2, df2], ignore_index=True)
    
    
    #third sheet details
    header_row_third_sheet=[["Date Format","M/d/yy h:mm a","MM Month, dd:Day, yy:year, mm:minute, hh:hours"],
                            ["Time Zone","(GMT-05:00) Eastern Time (US & Canada)","America/New_York"],
                            ["Empty Fields","[blank]","To remove existing values in character fields and leave them empty, place the value [blank] (including the brackets) in the respective cells on the import spreadsheet."]]
    
    final_df3 = pd.DataFrame(header_row_third_sheet)
    
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Changed to YYYYMMDD format which is more standard
    filename = f"inventory_export_{timestamp}.xlsx"
    print(f"Generated filename: {filename}")  # Debug output
    
    #memory buffer in which we will write the excel file
    output = io.BytesIO()
    
    #pd.excelwriter --> pandas functio which is used to write the dataframes to the excel file
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        final_df1.to_excel(writer, index=False,sheet_name='Data')
        final_df2.to_excel(writer, index=False,sheet_name='Detail')
        final_df3.to_excel(writer, index=False,header=False,sheet_name='Validations')
        
        
    output.seek(0)
    
    return send_file(
    output,
    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    as_attachment=True,
    download_name=filename
)


if __name__ == '__main__':
    insert_nextup() #Only runs if ASN is not inserted
    app.run()