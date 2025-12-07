import sqlite3
import os

def migrate():
    # 🚨 CAMBIO CRÍTICO: Especificar la ruta a la carpeta 'instance'
    DB_PATH = os.path.join('instance', 'termomaz.db') 
    
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database file not found at {DB_PATH}. Your application must create it first.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Connecting to: {DB_PATH}. Attempting to add 'paid_amount' column...")
    
    try:
        # Asegúrate de que la tabla 'order' exista antes de ALTER
        # Si aún obtienes 'no such table', debes ejecutar 'Base.metadata.create_all()' en tu app.py primero.
        
        # Agregar paid_amount
        cursor.execute('ALTER TABLE "order" ADD COLUMN paid_amount REAL')
        print("✅ Added paid_amount column.")
        
        # Agregar payment_status
        cursor.execute("ALTER TABLE \"order\" ADD COLUMN payment_status VARCHAR(20) DEFAULT 'Pending'")
        print("✅ Added payment_status column.")
            
        conn.commit()
        print("🎉 Migration committed successfully to the correct file.")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ Migration already performed.")
        elif "no such table" in str(e):
            print("🛑 Error: Table 'order' does not exist. Please initialize the database (run Base.metadata.create_all) and try again.")
        else:
            print(f"❌ Unhandled Operational Error: {e}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()