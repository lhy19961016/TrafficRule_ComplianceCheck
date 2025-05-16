import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, filedialog
import csv
from datetime import datetime
import os
import threading
from openai import OpenAI, Client

client = Client(
    base_url="https://api2.aigcbest.top/v1",
    api_key="sk-854gaFsTRtfpMPIWmMlHzCXiCGZX5Vy32ayOigQNs9kSvFFW"
)

class TrafficRuleTranslator:
    def __init__(self, root):
        self.root = root
        self.root.title("数字交规生成器 v1.0")
        self.root.geometry("900x750")
        
        self.setup_logging()
        
        self.csv_filename = "digital_traffic_rules.csv"
        self.init_database()
        
        self.create_widgets()
        
        self.client = client 

        self.generation_params = {
        'temperature': 0.2,        
        'top_p': 1.0,               
    }
                
    def setup_logging(self):
        """Configure proper logging system"""
        log_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        os.makedirs("logs", exist_ok=True)
        
        self.logger = logging.getLogger("TrafficRuleTranslator")
        self.logger.setLevel(logging.INFO)
        
        handler = RotatingFileHandler(
            "logs/traffic_rules.log",
            maxBytes=5*1024*1024,
            backupCount=3,
            encoding='utf-8'
        )
        handler.setFormatter(log_formatter)
        self.logger.addHandler(handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        self.logger.addHandler(console_handler)
    
    def init_database(self):
        # 获取当前脚本所在目录的绝对路径
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.csv_filename = os.path.join(base_path, "digital_traffic_rules.csv")
        
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Chinese Text", "English Translation", "MTL Formula"])

    def create_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        input_frame = tk.LabelFrame(main_frame, text="输入中文交规", padx=10, pady=10)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.input_text = scrolledtext.ScrolledText(input_frame, height=8, wrap=tk.WORD)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.translate_btn = tk.Button(
            btn_frame, 
            text="翻译并生成MTL", 
            command=self.start_processing_thread
        )
        self.translate_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = tk.Button(
            btn_frame,
            text="清除",
            command=self.clear_interface
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.progress = ttk.Progressbar(
            input_frame, 
            orient="horizontal",
            length=400, 
            mode="determinate"
        )
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.pack_forget()

        self.time_label = tk.Label(input_frame, text="预估等待时间: --")
        self.time_label.pack()
        self.time_label.pack_forget()
        
        display_frame = tk.LabelFrame(main_frame, text="翻译结果", padx=10, pady=10)
        display_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.notebook = ttk.Notebook(display_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        eng_frame = tk.Frame(self.notebook)
        tk.Label(eng_frame, text="英文翻译:", anchor='w').pack(fill=tk.X)
        self.english_display = scrolledtext.ScrolledText(
            eng_frame, 
            height=10, 
            state='disabled',
            wrap=tk.WORD
        )
        self.english_display.pack(fill=tk.BOTH, expand=True)
        self.notebook.add(eng_frame, text="英文翻译")
        
        mtl_frame = tk.Frame(self.notebook)
        tk.Label(mtl_frame, text="MTL语句:", anchor='w').pack(fill=tk.X)
        self.mtl_display = scrolledtext.ScrolledText(
            mtl_frame, 
            height=10, 
            state='disabled',
            wrap=tk.WORD
        )
        self.mtl_display.pack(fill=tk.BOTH, expand=True)
        self.notebook.add(mtl_frame, text="MTL语句")
        
        decision_frame = tk.Frame(main_frame)
        decision_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(decision_frame, text="是否加入数字交规库?").pack(side=tk.LEFT, padx=5)
        
        self.accept_btn = tk.Button(
            decision_frame, 
            text="加入", 
            command=lambda: self.save_rule(True),
            state='disabled'
        )
        self.accept_btn.pack(side=tk.LEFT, padx=5)
        
        self.reject_btn = tk.Button(
            decision_frame, 
            text="不加入", 
            command=lambda: self.save_rule(False),
            state='disabled'
        )
        self.reject_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_var = tk.StringVar()
        self.status_var.set("准备就绪")
        self.status_bar = tk.Label(
            self.root, 
            textvariable=self.status_var, 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, padx=10, pady=5)
    
    def start_processing_thread(self):
        """Start the processing in a separate thread"""
        chinese_text = self.input_text.get("1.0", tk.END).strip()
        if not chinese_text:
            messagebox.showwarning("警告", "请输入中文交规!")
            return
        

        self.translate_btn.config(state='disabled')
        self.clear_btn.config(state='disabled')
        self.progress.pack(fill=tk.X, pady=5)
        self.time_label.pack()
        self.progress["value"] = 0
        self.status_var.set("正在翻译...")
        
        threading.Thread(
            target=self.process_rule_with_estimation, 
            args=(chinese_text,),
            daemon=True
        ).start()
    
    def process_rule_with_estimation(self, chinese_text):
        """Process with time estimation for both phases"""
        try:
            self.root.after(0, lambda: self.status_var.set("正在翻译(阶段1/2)..."))
            
            chinese_char_count = len(chinese_text)
            trans_estimate = max(2, min(10, chinese_char_count / 15)) 
            
            english_text = self.translate_to_english(chinese_text)
            
            self.root.after(0, lambda: self.status_var.set("正在生成MTL(阶段2/2)..."))
        
            english_word_count = len(english_text.split())
            mtl_estimate = max(3, min(20, english_word_count / 4))  
            total_estimate = trans_estimate + mtl_estimate
            
            self.root.after(0, lambda: self.animate_progress(total_estimate))
            
            mtl_statement = self.generate_mtl_statement(english_text)
            
            self.root.after(0, lambda: [
                self.progress.config(value=100),
                self.time_label.pack_forget(),
                self.update_results(english_text, mtl_statement, chinese_text)
            ])
            
        except Exception as e:
            self.root.after(0, lambda error=e: [
                self.time_label.pack_forget(),
                self.handle_error(error)
            ])
    
    def animate_progress(self, total_time):
        """Animate progress bar based on estimated time"""
        if self.progress["value"] < 95:  
            elapsed_percent = self.progress["value"] / 100
            elapsed_time = elapsed_percent * total_time
            remaining_time = max(1, total_time - elapsed_time)
            
            mins, secs = divmod(int(remaining_time), 60)
            time_str = f"{mins}分{secs}秒" if mins else f"{secs}秒"
            self.time_label.config(text=f"预估剩余时间: {time_str}")
            
            increment = min(5, 100 - self.progress["value"])
            self.progress["value"] += increment

            interval = int((remaining_time / (100 - self.progress["value"])) * 1000)
            self.root.after(interval, lambda: self.animate_progress(total_time))
    
    def translate_to_english(self, text):
        """Translate Chinese to English using GPT-4"""
        response = self.client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1",
            messages=[
                {"role": "system", "content": "你是一名专业的交通法规翻译专家。请将以下中文交通规则准确翻译成英文，保持专业术语和技术细节的准确性。"},
                {"role": "user", "content": text}
            ],
            temperature=self.generation_params['temperature'],
            top_p=self.generation_params['top_p']
        )
        return response.choices[0].message.content
    
    def build_system_prompt(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base_path, "traffic_rules.csv")
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                prompt = """You are a traffic rules expert specialized in converting natural language traffic regulations to Metric Temporal Logic (MTL) formulas. Follow these guidelines:

                            1. Strictly adhere to the template format
                            2. Maintain predicate naming consistency
                            3. Handle temporal constraints and logical operators properly
                            4. Follow below template for MTL formalization.
                            If the interval is not specified for any operator, we assume that the interval is specified until the end. Where operator X means "next", U means "until", G means "globally", F means "finally", P means "previous". (other predicates are hidden for the illustration). The formula should only contain atomic propositions or logical and temporal operators: |, &, ~, ->, <->,X, G, F, O, P, U.
                            5. Please consider using quantifiable language: 1. at_intersection and at_traffic_light can be directly evaluated based on lane occupancy and sensor data.
                                                                                2. in_front(x, y) ⟺ (distance(x, y) ≤ d_th ∧ (lane_id(x) = lane_id(y))) with d_th = 1.0 meter (Euclidean distance). in_behind is defined similarly.
                                                                                3. stop(x) ⟺ -v_th ≤ velocity(x) ≤ v_th with v_th = 0.1 m/s.
                                                                                4. cross_stopLine(x) ⟺ position(x) > position(stopLine); position from sensor data.
                            I will give you some reference examples, as following:
                            """
                for idx, row in enumerate(reader, 1):
                    if None in row.values():  # 跳过空行
                        continue
                    prompt += f"\nExample {idx}:\n"
                    prompt += f"\nNatural Language Rule: {row['Natural Language Rule']}"
                    prompt += f"\nTought chain: {row['Step-by-Step Thought Process']}"
                    prompt += f"\nMTL Formula: {row['MTL Formula']}"
                    prompt += f"\n -------------------------------------------------------------------------------------------------------"
                prompt += "\n Now please convert the following new rule in natural language to MTL formula following the examples:"
                return prompt
        except Exception as e:
            self.logger.error("Error building system prompt: %s", str(e))
            return ""
        
    def generate_mtl_statement(self, english_text):
        """Generate MTL from English text using the loaded template"""
        prompt = self.build_system_prompt()
        response = self.client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Natural Language Rule: {english_text} \n MTL Formula:"}
            ],
            temperature=self.generation_params['temperature'],
            top_p=self.generation_params['top_p']
        )
        return response.choices[0].message.content.strip()
    
    def update_results(self, english_text, mtl_statement, chinese_text):
        """Update UI with results"""
        self.update_display(self.english_display, english_text)
        self.update_display(self.mtl_display, mtl_statement)
        
        self.accept_btn.config(state='normal')
        self.reject_btn.config(state='normal')
        self.translate_btn.config(state='normal')
        self.clear_btn.config(state='normal')
        
        self.current_data = {
            'chinese': chinese_text,
            'english': english_text,
            'mtl': mtl_statement
        }
        
        self.status_var.set("翻译完成 - 请选择是否加入库中")
        self.progress.pack_forget()
    
    def update_display(self, widget, content):
        """Update display widgets"""
        widget.config(state='normal')
        widget.delete('1.0', tk.END)
        widget.insert(tk.END, content)
        widget.config(state='disabled')
    
    def handle_error(self, error):
        """Handle errors in main thread"""
        messagebox.showerror("错误", f"处理过程中出错: {str(error)}")
        self.status_var.set(f"错误: {str(error)}")
        self.translate_btn.config(state='normal')
        self.clear_btn.config(state='normal')
        self.progress.pack_forget()
        self.logger.error("Processing error: %s", str(error))
    
    def save_rule(self, save_to_db):
        if not hasattr(self, 'current_data'):
            return
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = self.current_data
        
        if save_to_db:
            try:
                with open(self.csv_filename, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        timestamp,
                        data['chinese'],
                        data['english'],
                        data['mtl']
                    ])
                self.status_var.set("规则已保存到数字交规库")
                self.logger.info("Rule saved to database: %s", data['chinese'])
            except Exception as e:
                self.logger.error("Error saving to database: %s", str(e))
                messagebox.showerror("错误", f"保存到数据库失败: {str(e)}")
        else:
            self.logger.info(
                "Rejected Rule - Chinese: %s - English: %s - MTL: %s",
                data['chinese'],
                data['english'],
                data['mtl']
            )
            self.status_var.set("规则已记录到日志文件")
        
        self.clear_interface()
    
    def clear_interface(self):
        """Clear all inputs and results"""
        self.input_text.delete('1.0', tk.END)
        self.update_display(self.english_display, "")
        self.update_display(self.mtl_display, "")

        self.accept_btn.config(state='disabled')
        self.reject_btn.config(state='disabled')
        
        if hasattr(self, 'current_data'):
            del self.current_data
        
        self.status_var.set("准备就绪")

if __name__ == "__main__":
    import logging
    from logging.handlers import RotatingFileHandler
    
    root = tk.Tk()
    try:
        ttk.Style().theme_use('clam')
    except:
        pass
    
    app = TrafficRuleTranslator(root)
    root.mainloop()