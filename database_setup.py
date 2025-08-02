from config import conn

def setup_database(conn):  # now
    cursor = conn.cursor()
    # Enable pgvector extension
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # Create Skills table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS KBase (
            sid SERIAL PRIMARY KEY,
            problem TEXT,
            solution TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            vector_tags vector(768),
            UNIQUE (sid, problem)
        );
        """
    )
    
    # Create QuestionBank table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Tags (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        );
        """
    )

    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS KBaseTags (
        kbase_id INT REFERENCES KBase(sid) ON DELETE CASCADE,
        tag_id INT REFERENCES Tags(id) ON DELETE CASCADE,
        PRIMARY KEY (kbase_id, tag_id)
    );
    """
    )

    
    conn.commit()
    cursor.close()
    print("Database setup complete.")

setup_database(conn)
conn.close()