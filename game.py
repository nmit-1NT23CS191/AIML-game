import random
import tkinter as tk
from tkinter import messagebox


TOTAL_QUESTIONS = 10
QUESTION_DELAY_MS = 1500
AI_ACCURACY = 0.8
AI_TIME_MIN_SECONDS = 1.0
AI_TIME_MAX_SECONDS = 4.0

DIFFICULTY_RANGES = {
    "easy": (10, 10),
    "medium": (20, 15),
    "hard": (50, 20),
}

OPERATORS = ["+", "-", "*", "/"]


class ArithmeticChallengeApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Arithmetic Challenge Game")
        self.root.geometry("520x420")
        self.root.resizable(False, False)

        self.container = tk.Frame(root, padx=20, pady=20)
        self.container.pack(fill="both", expand=True)

        self.reset_game_state()
        self.show_name_screen()

    def reset_game_state(self) -> None:
        # Player and round setup.
        self.player_name = ""
        self.difficulty = ""

        # Question tracking.
        self.current_question = 0
        self.current_answer = 0
        self.question_start_ms = 0

        # Score tracking.
        self.player_total_time = 0.0
        self.ai_total_time = 0.0
        self.correct_count = 0
        self.wrong_count = 0
        self.ai_correct_count = 0
        self.ai_wrong_count = 0

        # Game flow control.
        self.game_active = True
        self.after_ids = []

    def clear(self) -> None:
        # Remove all widgets from the screen before building the next one.
        for widget in self.container.winfo_children():
            widget.destroy()

    def add_after(self, delay_ms: int, callback) -> None:
        after_id = self.root.after(delay_ms, callback)
        self.after_ids.append(after_id)

    def cancel_after(self) -> None:
        # Cancel any delayed callback that was scheduled during the round.
        for after_id in self.after_ids:
            try:
                self.root.after_cancel(after_id)
            except tk.TclError:
                pass
        self.after_ids.clear()

    def add_label(self, text: str, font: tuple[str, int, str] | tuple[str, int] = ("Arial", 12), **kwargs) -> tk.Label:
        return tk.Label(self.container, text=text, font=font, **kwargs)

    def add_button(self, text: str, command, **kwargs) -> tk.Button:
        return tk.Button(self.container, text=text, command=command, font=("Arial", 11, "bold"), **kwargs)

    def show_name_screen(self) -> None:
        # First screen: ask for the player's name.
        self.clear()
        self.add_label("🧮 Arithmetic Challenge", font=("Arial", 22, "bold")).pack(pady=(0, 20))
        self.add_label("Welcome! Enter your name to start.").pack(pady=(0, 10))

        self.name_entry = tk.Entry(self.container, font=("Arial", 12), width=28)
        self.name_entry.pack(pady=(0, 12))
        self.name_entry.bind("<Return>", lambda _event: self.start_game())
        self.name_entry.focus_set()

        self.add_button("Start Game", self.start_game).pack()

    def start_game(self) -> None:
        # Validate the player's name before continuing.
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showinfo("Missing name", "Please enter your name!")
            return

        self.player_name = name
        self.show_difficulty_screen()

    def show_difficulty_screen(self) -> None:
        # Second screen: choose how hard the questions should be.
        self.clear()
        self.add_label(f"Hello, {self.player_name}!", font=("Arial", 20, "bold")).pack(pady=(0, 12))
        self.add_label("Select Difficulty:").pack(pady=(0, 16))

        row = tk.Frame(self.container)
        row.pack(pady=8)

        difficulty_buttons = [
            ("😊 Easy", "easy"),
            ("😐 Medium", "medium"),
            ("😤 Hard", "hard"),
        ]

        for column, (button_text, level) in enumerate(difficulty_buttons):
            tk.Button(
                row,
                text=button_text,
                width=12,
                font=("Arial", 11),
                command=lambda chosen_level=level: self.start_round(chosen_level),
            ).grid(row=0, column=column, padx=8)

    def start_round(self, difficulty: str) -> None:
        # Reset everything for a new round, then show the game screen.
        self.difficulty = difficulty
        self.reset_round_data()
        self.cancel_after()
        self.show_game_screen()
        self.next_question()

    def reset_round_data(self) -> None:
        self.current_question = 0
        self.current_answer = 0
        self.question_start_ms = 0
        self.player_total_time = 0.0
        self.ai_total_time = 0.0
        self.correct_count = 0
        self.wrong_count = 0
        self.ai_correct_count = 0
        self.ai_wrong_count = 0
        self.game_active = True

    def show_game_screen(self) -> None:
        # Main game screen: question, answer box, and result message.
        self.clear()
        self.progress_label = self.add_label("", font=("Arial", 12, "bold"))
        self.progress_label.pack(pady=(0, 10))

        self.question_label = self.add_label("", font=("Arial", 20, "bold"))
        self.question_label.pack(pady=(0, 18))

        self.answer_entry = tk.Entry(self.container, font=("Arial", 12), width=20)
        self.answer_entry.pack(pady=(0, 12))
        self.answer_entry.bind("<Return>", lambda _event: self.submit_answer())

        self.add_button("Submit", self.submit_answer).pack(pady=(0, 12))

        self.result_label = self.add_label("", wraplength=460, justify="center")
        self.result_label.pack(pady=(10, 0))
        self.answer_entry.focus_set()

    def make_question(self) -> tuple[int, str, int, int]:
        # Generate numbers based on the selected difficulty.
        a_max, b_max = DIFFICULTY_RANGES.get(self.difficulty, DIFFICULTY_RANGES["easy"])
        a = random.randint(1, a_max)
        b = random.randint(1, b_max)
        op = random.choice(OPERATORS)

        # Keep division questions whole-number only.
        if op == "/":
            a *= b

        answer_map = {
            "+": a + b,
            "-": a - b,
            "*": a * b,
            "/": a // b,
        }
        answer = answer_map[op]

        return a, op, b, answer

    def next_question(self) -> None:
        # Stop when the round has reached the question limit.
        if self.current_question >= TOTAL_QUESTIONS:
            return self.end_game()

        self.current_question += 1
        a, op, b, self.current_answer = self.make_question()
        self.progress_label.config(text=f"Question {self.current_question} / {TOTAL_QUESTIONS}")
        self.question_label.config(text=f"{a} {op} {b}")
        self.result_label.config(text="")
        self.answer_entry.delete(0, tk.END)
        self.answer_entry.focus_set()
        self.question_start_ms = int(self.root.tk.call("clock", "milliseconds"))

    def submit_answer(self) -> None:
        # Ignore extra clicks after the game is over.
        if not self.game_active:
            return

        try:
            user_answer = int(self.answer_entry.get().strip())
        except ValueError:
            self.result_label.config(text="Please enter a valid whole number.")
            return

        user_time = (int(self.root.tk.call("clock", "milliseconds")) - self.question_start_ms) / 1000.0
        player_correct = user_answer == self.current_answer

        if player_correct:
            self.correct_count += 1
            self.player_total_time += user_time
            self.result_label.config(text=f"✅ Correct! Time: {user_time:.2f}s")
        else:
            self.wrong_count += 1
            self.result_label.config(text="❌ Your answer is wrong! Moving to next question...")

        self.play_ai(user_time, player_correct)

    def play_ai(self, user_time: float, player_correct: bool) -> None:
        # Simulate the AI answering the same question.
        ai_time = random.uniform(AI_TIME_MIN_SECONDS, AI_TIME_MAX_SECONDS)
        ai_correct = random.random() < AI_ACCURACY

        if ai_correct:
            self.ai_correct_count += 1
            self.ai_total_time += ai_time
        else:
            self.ai_wrong_count += 1

        if player_correct:
            self.add_after(
                int(ai_time * 1000),
                lambda: self.show_ai_result(user_time, ai_time, ai_correct),
            )
        else:
            self.add_after(QUESTION_DELAY_MS, self.next_question)

    def show_ai_result(self, user_time: float, ai_time: float, ai_correct: bool) -> None:
        if self.game_active:
            if ai_correct:
                text = f"✅ Correct! Your: {user_time:.2f}s | AI: {ai_time:.2f}s"
            else:
                text = f"✅ Correct! AI wrong. Your: {user_time:.2f}s | AI: Wrong"

            self.result_label.config(text=text)
            self.add_after(QUESTION_DELAY_MS, self.next_question)

    def winner_text(self) -> str:
        # First compare correct answers, then compare total time if needed.
        if self.correct_count != self.ai_correct_count:
            if self.correct_count > self.ai_correct_count:
                return "🎉 YOU WIN! You have more correct answers."
            return "🤖 AI WINS! AI has more correct answers."

        if self.player_total_time != self.ai_total_time:
            if self.player_total_time < self.ai_total_time:
                return "🎉 YOU WIN! Correct answers tied, but you were faster."
            return "🤖 AI WINS! Correct answers tied, AI was faster."

        return "🤝 TIE! Same correct answers and same time."

    def end_game(self) -> None:
        # Show the final summary screen.
        self.game_active = False
        self.cancel_after()
        self.clear()

        summary_lines = [
            ("🏁 Challenge Complete!", ("Arial", 20, "bold")),
            (f"Player: {self.player_name} | Difficulty: {self.difficulty.upper()}", ("Arial", 12)),
            (f"Your Total Time: {self.player_total_time:.2f}s | AI Total Time: {self.ai_total_time:.2f}s", ("Arial", 12)),
            (f"Player - Correct: {self.correct_count} | Wrong: {self.wrong_count}", ("Arial", 12)),
            (f"AI - Correct: {self.ai_correct_count} | Wrong: {self.ai_wrong_count}", ("Arial", 12)),
            (self.winner_text(), ("Arial", 13, "bold")),
        ]

        for text, font in summary_lines:
            self.add_label(text, font=font, wraplength=460, justify="center").pack(pady=(0, 8))

        self.add_button("Play Again", self.show_difficulty_screen).pack(pady=(10, 0))


if __name__ == "__main__":
    root = tk.Tk()
    ArithmeticChallengeApp(root)
    root.mainloop()
