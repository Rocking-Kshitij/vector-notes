import tkinter as tk
from abc import ABC, abstractmethod
from backend_logic import DictionaryActionFactory


# ----------------------------
# GUI WRAPPED IN A CLASS
# ----------------------------

class DictionaryApp:
    def __init__(self):
        self.root = tk.Tk()
        self.typing_timer = None
        self.selected_window = None
        self.action = "search"
        self.search_func = True
        self.vector_search = True
        self.resultbox_state = ""
        self.result_box_dimen = []
        self.result_box_content_layout = []
        self.add_action = DictionaryActionFactory.get_action("add")
        self.safe_to_exit = True

        self.data_dict = {
            "sid": "",
            "problem_suggestion": [[], [], [], []], #[[problems], [solutions], [sids]]
            "problem": "",
            "result":"",
            "description": "",
            "tags": [],
            "tags_suggestion": []
        }

        self._setup_window()
        self._create_widgets()
        self._layout_widgets()
        self._binding_widgets()
        self.set_auto_search(True)

    def _setup_window(self):
        self.root.title("Resizable Dictionary App")
        self.root.geometry("600x350")
        self.root.minsize(400, 250)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=1)
        self.root.rowconfigure(6, weight=0)
        self.root.rowconfigure(7, weight=0)
        self.root.rowconfigure(8, weight=0)
        self.root.rowconfigure(9, weight=0)

    def _create_widgets(self):
        self.label = tk.Label(self.root, text="Enter word:", font=("Arial", 12))
        self.entry = tk.Entry(self.root, font=("Arial", 12))
        

        self.button_frame = tk.Frame(self.root)
        self.add_btn = tk.Button(self.button_frame, text="Add", command=self.on_add)
        self.remove_btn = tk.Button(self.button_frame, text="Remove", command=self.on_remove)
        self.search_btn = tk.Button(self.button_frame, text="Search", command=self.search_toggle)
        self.clear_btn = tk.Button(self.button_frame, text="Clear", command=self.clear_entry)
        self.copy_btn = tk.Button(self.button_frame, text="Copy", command=self.copy_to_clipboard)
        self.quit_btn = tk.Button(self.button_frame, text="Quit", command=self.graceful_quit)
        self.vect_btn = tk.Button(self.button_frame, text="Vector", command=self.vector_toggle)
        self.back_btn = tk.Button(self.button_frame, text = "Back", command=self.on_backbtn_select)

        self.result_box = tk.Text(self.root, font=("Arial", 12), wrap="word")

        self.tags_frame = tk.Frame(self.root)
        self.tags_label = tk.Label(self.tags_frame, text="Tags: ", font=("Arial", 12))
        self.tags_entry = tk.Entry(self.tags_frame, font=("Arial", 12))
        self.tags_label.pack(side="left")
        self.tags_entry.pack(side="left", fill="x", expand=True)


        self.tags_listbox_frame = tk.Frame(self.root)
        self.tags_listbox = tk.Listbox(
            self.tags_listbox_frame, 
            font=("Arial", 12), 
            height=1, 
            bd=1, 
            relief="solid", 
            yscrollcommand=lambda *args: self.tags_scrollbar.set(*args)
        )
        self.tags_listbox.pack(side="left", fill="both", expand=True)
        self.tags_scrollbar = tk.Scrollbar(
            self.tags_listbox_frame, 
            orient="vertical", 
            command=self.tags_listbox.yview
        )
        self.tags_scrollbar.pack(side="right", fill="y")


        self.status_label = tk.Label(self.root, text="", anchor="w", font=("Arial", 10), fg="gray")

        self.tags_spacer  = tk.Frame(self.root, height =9)

        self.bottom_spacer = tk.Frame(self.root, height=1)

    def _layout_widgets(self):
        self.label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 2))
        self.entry.grid(row=1, column=0,columnspan=2, sticky="ew", padx=10)


        self.button_frame.grid(row=3, column=0,columnspan=2, pady=5)
        for btn in [self.add_btn, self.remove_btn, self.search_btn, self.clear_btn, self.copy_btn, self.quit_btn, self.vect_btn, self.back_btn]:
            btn.pack(side="left", padx=5)
        self.result_box.grid(row=4, column=0,columnspan=2, sticky="nsew", padx=10, pady=10)

        self.tags_frame.grid(row=6, column=0, columnspan=2, sticky="ew",padx=10, pady=5)

        self.tags_listbox_frame.grid(row=7, column=0, columnspan=2, sticky="ew", padx=10)

        self.status_label.grid(row=8, column=0, columnspan=2, sticky="we", padx=10, pady=5)
        self.tags_spacer.grid(row=9,column=0, columnspan=2, sticky="we", padx=10, pady=5)
        self.bottom_spacer.grid(row=10,column=0, columnspan=2, sticky="we", padx=10, pady=5)

        self.listbox_show("tags", False)



    def _binding_widgets(self):
        self.tags_listbox.bind("<<ListboxSelect>>", lambda event: self.on_listbox_select(event, "tags"))

        self.tags_entry.bind("<FocusOut>", lambda event: self.listbox_show("tags", False))

        self.tags_entry.bind("<FocusIn>", lambda event: self.listbox_show("tags", True))

        self.tags_entry.bind("<Down>", lambda event: self.handle_enter_key(self.tags_listbox, "tags"))

        self.result_box.bind("<Button-1>", self.on_text_click)

        self.result_box.bind("<Configure>", self.on_resize)
    
    def search_toggle(self):
        self.action = "search"
        self.set_auto_search(True)#if autosearch activated on search action
        self.clear_entry()
        self.update_status("Search Activated")

    def on_remove(self):
        if self.resultbox_state == "showing_result":
            DictionaryActionFactory.get_action("remove").execute(self)
            self.clear_entry()
            self.update_status("Removed")
        else: 
            self.update_status("Remove Activated")
            self.set_auto_search(True)

    def on_add(self):
        self.set_auto_search(False)
        if self.action != "add":
            self.clear_entry()
            self.update_status("Add Activated")
            self.action = "add"
        else:
            self.add_action.execute(self) # Sending to action factory

    def handle_enter_key(self, listbox, listboxtype):
        if not listbox.curselection():
            listbox.selection_set(tk.ACTIVE)

        event = tk.Event()
        event.widget = listbox
        self.on_listbox_select(event, listboxtype)

    def on_backbtn_select(self):
        if self.resultbox_state == "showing_result":
            self.resultbox_state = "showing_suggestions"
            self.resultbox_decorator(trigger="first_trigger")

    def on_resize(self, event):
        self.result_box_dimen = [int(event.width), event.height]
        if self.resultbox_state == "showing_suggestions":
            self.resultbox_decorator(trigger="on_resize")
        elif self.resultbox_state == "showing_result":
            char_width, char_height = self.result_box_dimen
            edge_value = ("="*int(char_width/10))
            self.update_resultbox(self.data_dict["problem"]+"\n"+edge_value+"\n"+self.data_dict["result"])


    def update_resultbox(self, text):
        self.result_box.config(state='normal')
        self.result_box.delete("1.0", tk.END)
        self.result_box.insert(tk.END, text)
        self.result_box.config(state='normal')

    def resultbox_decorator(self, trigger = "any"):
        if self.resultbox_state != "showing_suggestions":
            return
        if trigger == "first_trigger":
            self.result_box_dimen = [self.result_box.winfo_width(), self.result_box.winfo_height()]
        char_width, char_height = self.result_box_dimen
        self.result_box_content_layout = [0]

        keys , values, sids, description = self.data_dict["problem_suggestion"]
        edge_value = ("="*int(char_width/10))
        str_value = ""
        for i in range(min(len(keys), 10)):
            key = keys[i]
            # lines = values[i].splitlines()
            # while len(lines) <3:
            #     lines.append("")
            # value = "\n".join(lines[:3])
            value = values[i].splitlines()[:3]
            for j in range(len(value)):
                max_len = int(len(edge_value) *1.3)
                if len(value[j]) > (max_len):
                    value[j]= value[j][0:max_len]
            value = "\n".join(value)
            str_value = str_value + edge_value + "\n"+key+ "\n" +"\n" + value +"\n"
            self.result_box_content_layout.append(len(str_value.splitlines()))
        str_value += edge_value
        self.update_resultbox(str_value)

    def listbox_show(self, listbox, show):
        if listbox == "tags":
            if show:
                self.tags_listbox_frame.grid(row=7, column=0, columnspan=2, sticky="ew", padx=10)
                self.tags_spacer.grid_remove() 
                self.status_label.grid_remove() 
            else:
                self.status_label.grid()
                self.tags_spacer.grid()
                self.tags_listbox_frame.grid_remove() 

    def on_text_click(self, event):
        if self.resultbox_state not in ["showing_suggestions"]:
            return
        self.resultbox_state = "showing_result"
        index = self.result_box.index(f"@{event.x},{event.y}")
        index = int(index.split(".")[0]) -1
        char_width, char_height = self.result_box_dimen
        edge_value = ("="*int(char_width/10))
        # print(event.x)
        # print(event.y)
        for i in range(len(self.result_box_content_layout)-1):
            if (index>self.result_box_content_layout[i]) and (index <self.result_box_content_layout[i+1]):
                keys , values , sids, description = self.data_dict["problem_suggestion"]
                self.data_dict["problem"] = keys[i]
                self.data_dict["result"] = values[i]
                self.data_dict["sid"] = sids[i]
                self.data_dict["description"] = description[i]
                self.update_resultbox(self.data_dict["problem"]+ "\n"+edge_value+"\n"+ self.data_dict["result"] + "\n"+edge_value+"\n" + self.data_dict["description"].replace("**", ""))

    # moving suggestion to entry once selected
    def on_listbox_select(self, event, listboxtype):#
        list_box = event.widget
        if list_box == self.tags_listbox and self.tags_listbox.curselection():
            selected_tag = self.tags_listbox.get(self.tags_listbox.curselection())
            #------------
            # Get current tags from the entry box and split by ":"
            current_tags = self.tags_entry.get().split(":")

            # Replace the last tag (incomplete one being typed) with the selected suggestion
            current_tags[-1] = selected_tag
            self.data_dict["tags"] = current_tags

            # new tag string
            new_tags_string = ":".join(current_tags) + ":"
            #-------------------------
            self.tags_entry.delete(0, tk.END)
            self.tags_entry.insert(0, new_tags_string)

            # removing from listbox
            self.tags_listbox.delete(0, tk.END)
            self.tags_listbox.insert(tk.END, "")
            self.tags_listbox_frame.grid()
            # self.listbox_show("tags",False)

    def update_status(self, message):
        self.status_label.config(text=message)

    def perform_action(self, action_type):
        pass
        # self.set_auto_search(False)
        # if self.action != action_type:
        #     self.clear_entry()
        #     self.update_status(f"{action_type.capitalize()} Activated")
        #     self.action = action_type
        # else:
        #     action = DictionaryActionFactory.get_action(action_type) # Sending to action factory
        #     action.execute(self)
    

    def after_search(self):
        if self.selected_window == "entry":
            self.resultbox_state = "showing_suggestions"
            self.resultbox_decorator("first_trigger")

        elif self.selected_window == "tags":
            values = self.data_dict["tags_suggestion"]
            self.tags_listbox.delete(0, tk.END)
            for item in values:
                self.tags_listbox.insert(tk.END, item)
            self.tags_listbox_frame.grid()

    #triggers autosearch if key released
    def on_key_release(self, event):
        # event.widget
        element = event.widget
        # element = str(self.root.focus_get())
        if element == self.entry:
            self.selected_window = "entry"
            query = self.entry.get()
            if not query:
                return
        elif element == self.tags_entry:
            self.selected_window = "tags"
            query = self.tags_entry.get()
            if not query:
                self.listbox_show("tags",False)
                return
        
        if self.typing_timer:
            self.root.after_cancel(self.typing_timer)
        self.typing_timer = self.root.after(200, lambda: DictionaryActionFactory.get_action("autocomplete").execute(self))

    #toggles autosearch functionality
    def set_auto_search(self, enable):
        if enable:
            # self.entry.bind("<Return>", lambda event: self.perform_action("search"))
            self.entry.bind("<KeyRelease>", lambda event: self.on_key_release(event))
            self.tags_entry.bind("<KeyRelease>", lambda event: self.on_key_release(event))
        else:
            # self.entry.unbind("<Return>")
            self.entry.unbind("<KeyRelease>")
            self.tags_entry.unbind("<KeyRelease>")
            self.selected_window = None

    def clear_entry(self):
        self.entry.delete(0, tk.END)
        self.result_box.delete("1.0", tk.END)
        self.tags_entry.delete(0, tk.END)
        self.listbox_show("entry", False)
        self.listbox_show("tags", False)
        self.update_status("Cleared")
        self.resultbox_state = ""

    def copy_to_clipboard(self):
        result_text = self.result_box.get("1.0", tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(result_text)
        self.root.update()

    def graceful_quit(self):
        if self.safe_to_exit:
            self.update_status("Quitting")
            self.root.destroy()
        else:
            self.update_status("Please wait")

    def vector_toggle(self):
        self.vector_search = not(self.vector_search)
        if self.vector_search:
            self.update_status("Vector search enabled")
        else:
            self.update_status("Vector search disabled")


    def run(self):
        self.root.mainloop()
