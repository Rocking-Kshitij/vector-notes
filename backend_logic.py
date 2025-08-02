from abc import ABC, abstractmethod
import tkinter as tk
from config import conn, embeddings
import threading, time, queue
from llm_prompts import get_question_chain, get_description_chain

llm_executing = None
llm_executing_lock = threading.Lock()


# ----------------------------
# STRATEGY PATTERN COMPONENTS
# ----------------------------

class DictionaryAction(ABC):
    @abstractmethod
    def execute(self, app):
        pass

class Autocomplete(DictionaryAction):
    def execute(self, app):
        tag_list = app.tags_entry.get().split(":")
        last_tag = tag_list[-1]
        cursor = conn.cursor()

        if app.selected_window == "entry":
            if "" in tag_list:
                tag_list.remove("")
            problem = app.entry.get()
            if app.vector_search:
                result = self.vector_search(cursor, problem, tag_list)
            else:
                result = self.non_vector_search(cursor, problem, tag_list)
            app.data_dict["problem_suggestion"] = [[value[0] for value in result], [value[1] for value in result], [value[2] for value in result] , [value[3] for value in result]]
        elif app.selected_window == "tags" and last_tag!="":
            # app.listbox_show("tags", True)
            result = self.tags_search(cursor,last_tag)
            app.data_dict["tags_suggestion"] = [value[0] for value in result]
        else:
            print("None")
        app.after_search()
        cursor.close()

    def non_vector_search(self,cursor, problem, tag_list):
        if len(tag_list)!=0:
            placeholders = ','.join(['%s'] * len(tag_list))
            query = f"""
            SELECT k.problem, k.solution, k.sid
            FROM KBase k
            JOIN KBaseTags kt ON k.sid = kt.kbase_id
            JOIN Tags t ON kt.tag_id = t.id
            WHERE t.name IN ({placeholders})
            AND k.problem ILIKE %s
            GROUP BY k.sid, k.problem, k.solution
            HAVING COUNT(DISTINCT t.name) = %s
            ORDER BY similarity(k.problem, %s) DESC;
            """
            cursor.execute(query, tag_list + [f"%{problem}%", problem])
        else:
            cursor.execute("""
            SELECT k.problem, k.solution, k.sid
            FROM KBase k
            WHERE problem ILIKE %s
            ORDER BY similarity(k.problem, %s) DESC;
            """, (f"%{problem}%", problem))

        results = cursor.fetchall()
        return results

    def vector_search(self,cursor, problem, tag_list):
        vector_data = embeddings.embed_query(problem)

        if len(tag_list)!= 0:
            placeholders = ', '.join(['%s'] * len(tag_list))
            query = f"""
            WITH matching_sids AS (
                SELECT kb.sid, kb.problem, kb.solution, kb.vector_tags, tg.id, tg.name
                FROM kbase kb
                JOIN kbasetags kt ON kb.sid = kt.kbase_id
                JOIN tags tg ON kt.tag_id = tg.id
            ),
            matching_sids_tag1 AS (
                SELECT sid
                FROM matching_sids
                WHERE name IN ({placeholders})
                GROUP BY sid
                HAVING COUNT(DISTINCT name) = %s
            )

            select problem, solution,sid, Description, vector_tags <=> %s::vector as similarity
            FROM(
            SELECT distinct(sid), problem, solution, vector_tags 
            FROM matching_sids 
            WHERE sid IN (SELECT sid FROM matching_sids_tag1)
            )
            ORDER BY similarity
            LIMIT 10;
            """
            params = tag_list + [len(tag_list)] + [vector_data]
            params = tuple(params) # correct order!
            cursor.execute(query, params)
        else:
            cursor.execute("""
            SELECT k.problem, k.solution,k.sid, k.Description, k.vector_tags <=> %s::vector as similarity
            FROM KBase k
            ORDER BY similarity
            LIMIT 10;
            """, (vector_data,))
        return cursor.fetchall()


    def tags_search(self,cursor, tag):
        cursor.execute(
        "SELECT name FROM Tags WHERE name ILIKE %s;",
        (tag + '%',)
        )
        result = cursor.fetchall()
        return result

class AddAction(DictionaryAction):
    _task_queue = queue.Queue()
    _thread_started = False
    _lock = threading.Lock()

    def __init__(self):
        with AddAction._lock:
            if not AddAction._thread_started:
                thread = threading.Thread(target=self.add_data, daemon=True)
                thread.start()
                AddAction._thread_started = True

    def execute(self, app):
        problem = app.entry.get()
        solution = app.result_box.get("1.0", tk.END)
        tag_list = app.tags_entry.get().split(":")
        # if problem == "":
        #     app.update_status("No data")
        # else:
        self._task_queue.put([problem, solution, tag_list, app])
        print("added to queue", problem, flush = True)
        # self.add_data(problem, solution, tag_list)
        app.clear_entry()
        app.update_status("Insertion initiated")
        app.safe_to_exit = False
    def add_data(self):
        while True:
            task = self._task_queue.get()
            if task is None:
                print("[Background Thread] Stop signal received.")
                break  # Optional stop logic


            [key, value, tag_list,app] = task
            if key == "":
                key = get_question_chain.invoke({"content": value})
            description = get_description_chain.invoke({"problem": key, "solution": value})
            print(key, "\n", value, "\n", description)
            time.sleep(10)

            cursor = conn.cursor()
            
            self.add_tags(tag_list, cursor)
            conn.commit()

            self.add_kbase(key, value, description, cursor)
            conn.commit()

            self.add_kbasetags(key, tag_list, cursor)
            conn.commit()

            self.clean_tags(cursor)
            conn.commit()

            # cursor.close()
            self._task_queue.task_done()
            if AddAction._task_queue.qsize() == 0:
                app.safe_to_exit = True
    #Data base functions
    def add_tags(self, tag_list, cursor):
        for tag in tag_list:
            cursor.execute(
            """
            INSERT INTO Tags (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING;
            """,
            (tag,)
            )
    def add_kbase(self, key, value, description,  cursor):
        # Check if the problem exists
        cursor.execute(
        "SELECT solution FROM KBase WHERE problem = %s;",
        (key,)
        )
        result1 = cursor.fetchone()
        cursor.execute(
        "SELECT solution FROM KBase WHERE solution = %s;",
        (value,)
        )
        result2 = cursor.fetchone()

        if result1 is None and result2 is None:
            vector_data = embeddings.embed_query(key + value + description)
            # New problem – Insert
            cursor.execute(
                """
                INSERT INTO KBase (problem, solution, Description, vector_tags)
                VALUES (%s, %s, %s, %s);
                """,
                (key, value, description, vector_data)
            )
        elif result[0] != value:
            vector_data = embeddings.embed_query(key + value + description)
            # Existing problem, different solution – Update
            cursor.execute(
                """
                UPDATE KBase
                SET solution = %s,
                    Description = %s,
                    vector_tags = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE problem = %s;
                """,
                (value, description, vector_data, key)
            )
    def add_kbasetags(self, key, tag_list, cursor):
        cursor.execute(
        "SELECT sid FROM KBase WHERE problem = %s;",
        (key,))
        kbase_id = cursor.fetchone()[0]

        cursor.execute("SELECT tag_id FROM KBaseTags WHERE kbase_id = %s;", (kbase_id,))
        current_tag_ids = {row[0] for row in cursor.fetchall()}

        new_tag_ids = set()
        for tag_name in tag_list:
            cursor.execute("SELECT id FROM Tags WHERE name = %s;", (tag_name,))
            tag_id = cursor.fetchone()[0]
            new_tag_ids.add(tag_id)


        for tag_id in new_tag_ids - current_tag_ids:
            cursor.execute("""
            INSERT INTO KBaseTags (kbase_id, tag_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
            """, (kbase_id, tag_id))

        for tag_id in current_tag_ids - new_tag_ids:
            cursor.execute("""
            DELETE FROM KBaseTags
            WHERE kbase_id = %s AND tag_id = %s;
            """, (kbase_id, tag_id))
    def clean_tags(self, cursor):
        cursor.execute("""
        DELETE FROM Tags
        WHERE id NOT IN (
        SELECT DISTINCT tag_id FROM KBaseTags);
            """)
    


class RemoveAction(DictionaryAction):
    def execute(self, app):
        cursor = conn.cursor()
        word = app.data_dict["problem"]
        sid = app.data_dict["sid"]
        app.clear_entry()
        app.update_status("Data Removed")
        try:
            self.delete_data(cursor,sid)
            conn.commit()
            self.clean_tags(cursor)
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("Error:", e)
        finally:
            cursor.close()
        

    def delete_data(self,cursor, sid):
        cursor.execute("DELETE FROM KBase WHERE sid = %s;", (sid,))

    def clean_tags(self, cursor):
        cursor.execute("""
        DELETE FROM Tags
        WHERE id NOT IN (
        SELECT DISTINCT tag_id FROM KBaseTags);
            """)

# # ----------------------------
# # FACTORY METHOD
# # ----------------------------

class DictionaryActionFactory:
    @staticmethod
    def get_action(action_type: str) -> DictionaryAction:
        action_type = action_type.lower()
        if action_type == "autocomplete":
            return Autocomplete()
        elif action_type == "add":
            return AddAction()
        elif action_type == "remove":
            return RemoveAction()
        else:
            raise ValueError(f"Unknown action: {action_type}")
