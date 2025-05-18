import psycopg2
from psycopg2 import Error

# Add this function to handle database connection and fetch specific records from patients table
def fetch_patients_data():
    connection = None  # Initialize connection outside try block
    try:
        connection = psycopg2.connect(
            host="localhost",
            port="5433",
            database="Bevi_DB",
            user="postgres",
            password="pa$$word"  # Explicitly set empty password
        )
        print("✅ Connected to PostgreSQL successfully")
        
        cursor = connection.cursor()
        cursor.execute("""
            SELECT * FROM public.patients
            WHERE bill_paid = FALSE
            AND bill_date > (CURRENT_DATE - INTERVAL '6 months')
            AND message_sent = FALSE
            AND email_sent = FALSE
            AND reply_pending = FALSE
            AND conversation_status != 'resolved'
        """)
        patients_data = cursor.fetchall()
        print(patients_data)
        print("✅ Fetched data from patients table successfully")
        return patients_data
    except Error as e:
        print(f"❌ Error connecting to PostgreSQL or fetching data: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("✅ PostgreSQL connection closed")