let currentAnswer;
let startTime;
let currentQuestion = 0;
const TOTAL_QUESTIONS = 10;
let playerTotalTime = 0;
let aiTotalTime = 0;
let gameActive = true;
let difficulty = "";
let playerName = "";
let correctCount = 0;
let wrongCount = 0;
let aiCorrectCount = 0;
let aiWrongCount = 0;

function startWithName() {
    let name = document.getElementById("playerName").value.trim();
    
    if (name === "") {
        alert("Please enter your name!");
        return;
    }
    
    playerName = name;
    
    // Hide name section, show difficulty section
    document.getElementById("nameSection").classList.add("hidden");
    document.getElementById("difficultySection").classList.remove("hidden");
}

function selectDifficulty(level, buttonEl) {
    difficulty = level;

    // Highlight selected difficulty
    document.querySelectorAll(".diff-btn").forEach(btn => btn.classList.remove("active"));
    if (buttonEl) {
        buttonEl.classList.add("active");
    }

    // Reset game variables for a new round
    resetRoundState();

    // Hide difficulty section, show game section
    document.getElementById("difficultySection").classList.add("hidden");
    document.getElementById("gameSection").classList.remove("hidden");

    // Start game immediately
    generateQuestion();
}

function resetRoundState() {
    currentQuestion = 0;
    playerTotalTime = 0;
    aiTotalTime = 0;
    correctCount = 0;
    wrongCount = 0;
    aiCorrectCount = 0;
    aiWrongCount = 0;
    gameActive = true;
}

function generateQuestion() {
    if (currentQuestion >= TOTAL_QUESTIONS) {
        endGame();
        return;
    }

    currentQuestion++;
    let a, b;
    
    // Set ranges based on difficulty
    if (difficulty === "easy") {
        a = Math.floor(Math.random() * 10) + 1;      // 1-10
        b = Math.floor(Math.random() * 10) + 1;      // 1-10
    } else if (difficulty === "medium") {
        a = Math.floor(Math.random() * 20) + 1;      // 1-20
        b = Math.floor(Math.random() * 15) + 1;      // 1-15
    } else if (difficulty === "hard") {
        a = Math.floor(Math.random() * 50) + 1;      // 1-50
        b = Math.floor(Math.random() * 20) + 1;      // 1-20
    }
    
    let ops = ['+', '-', '*', '/'];
    let op = ops[Math.floor(Math.random() * ops.length)];

    // Avoid decimal division
    if (op === '/') {
        // Make dividend a multiple of divisor so answer is always an integer
        a = a * b;
    }

    let question = `${a} ${op} ${b}`;
    currentAnswer = eval(question);

    document.getElementById("progress").innerText = `Question ${currentQuestion} / ${TOTAL_QUESTIONS}`;
    document.getElementById("question").innerText = question;
    document.getElementById("result").innerText = "";
    document.getElementById("answer").value = "";
    document.getElementById("answer").focus();

    startTime = new Date().getTime();
}

function submitAnswer() {
    if (!gameActive) return;

    let userAnswer = Number(document.getElementById("answer").value);
    let endTime = new Date().getTime();
    let userTime = (endTime - startTime) / 1000;
    let playerCorrect = userAnswer === currentAnswer;

    if (playerCorrect) {
        correctCount++;
        playerTotalTime += userTime;
        document.getElementById("result").innerText = `✅ Correct! Time: ${userTime.toFixed(2)}s`;
    } else {
        wrongCount++;
        document.getElementById("result").innerText = "❌ Your answer is wrong! Moving to next question...";
    }

    playWithAI(userTime, playerCorrect);
}

function playWithAI(userTime, playerCorrect) {
    let aiTime = Math.random() * 3 + 1; // 1–4 sec
    let aiCorrect = Math.random() < 0.8; // 80% accuracy

    if (aiCorrect) {
        aiCorrectCount++;
        aiTotalTime += aiTime;
    } else {
        aiWrongCount++;
    }

    if (playerCorrect) {
        setTimeout(() => {
            if (!aiCorrect) {
                document.getElementById("result").innerText = `✅ Correct! AI wrong. Your: ${userTime.toFixed(2)}s | AI: Wrong`;
            } else {
                document.getElementById("result").innerText = `✅ Correct! Your: ${userTime.toFixed(2)}s | AI: ${aiTime.toFixed(2)}s`;
            }

            setTimeout(() => {
                generateQuestion();
            }, 1500);
        }, aiTime * 1000);
    } else {
        // For wrong player answer, move quickly to next question and only show wrong message.
        setTimeout(() => {
            generateQuestion();
        }, 1500);
    }
}

function endGame() {
    gameActive = false;

    // Hide game section, show result section
    document.getElementById("gameSection").classList.add("hidden");
    document.getElementById("resultSection").classList.remove("hidden");

    // Display results
    document.getElementById("playerInfo").innerText = `Player: ${playerName} | Difficulty: ${difficulty.toUpperCase()}`;

    let playerResult = `Your Total Time: ${playerTotalTime.toFixed(2)}s`;
    let aiResult = `AI Total Time: ${aiTotalTime.toFixed(2)}s`;
    document.getElementById("times").innerText = `${playerResult} | ${aiResult}`;

    document.getElementById("stats").innerText = `Player - Correct: ${correctCount} | Wrong: ${wrongCount}`;
    document.getElementById("aiStats").innerText = `AI - Correct: ${aiCorrectCount} | Wrong: ${aiWrongCount}`;

    // Winner rule: highest correct answers wins. If equal correct, lower time wins.
    if (correctCount > aiCorrectCount) {
        document.getElementById("winner").innerText = "🎉 YOU WIN! You have more correct answers.";
    } else if (aiCorrectCount > correctCount) {
        document.getElementById("winner").innerText = "🤖 AI WINS! AI has more correct answers.";
    } else {
        if (playerTotalTime < aiTotalTime) {
            document.getElementById("winner").innerText = "🎉 YOU WIN! Correct answers tied, but you were faster.";
        } else if (aiTotalTime < playerTotalTime) {
            document.getElementById("winner").innerText = "🤖 AI WINS! Correct answers tied, AI was faster.";
        } else {
            document.getElementById("winner").innerText = "🤝 TIE! Same correct answers and same time.";
        }
    }
}

function playAgain() {
    // Keep same name, ask only difficulty for replay
    resetRoundState();

    document.getElementById("resultSection").classList.add("hidden");
    document.getElementById("gameSection").classList.add("hidden");
    document.getElementById("difficultySection").classList.remove("hidden");
}