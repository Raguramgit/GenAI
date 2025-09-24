import streamlit as st
import random

# --- Constants ---
BOARD_SIZE = 3
SYMBOLS = ["❌", "⭕", "⭐", "❤️", "🐶", "🐱", "🦄", "🍕", "🌈", "🎈"]

# --- Background Styling ---
def set_background():
    st.markdown(
        """
        <style>
        .stApp {
            background-image: url("https://images.pexels.com/photos/139325/pexels-photo-139325.jpeg");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

set_background()

# --- Session State Initialization ---
if "board" not in st.session_state:
    st.session_state.board = [["" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
if "moves" not in st.session_state:
    st.session_state.moves = []
if "results" not in st.session_state:
    st.session_state.results = []
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "player1_symbol" not in st.session_state:
    st.session_state.player1_symbol = SYMBOLS[0]
if "player2_symbol" not in st.session_state:
    st.session_state.player2_symbol = SYMBOLS[1]
if "bot_symbol" not in st.session_state:
    st.session_state.bot_symbol = random.choice(SYMBOLS)

# --- Sidebar: Game Setup ---
st.sidebar.title("🎮 Game Setup")
mode = st.sidebar.radio("Choose Mode", ["2 Player", "1 Player vs Bot"])

player1 = st.sidebar.text_input("Player 1 Name", value="Player 1")
st.sidebar.markdown("#### Player 1 Symbol")
st.session_state.player1_symbol = st.sidebar.selectbox("Choose Symbol", SYMBOLS, index=0)

if mode == "2 Player":
    player2 = st.sidebar.text_input("Player 2 Name", value="Player 2")
    st.sidebar.markdown("#### Player 2 Symbol")
    st.session_state.player2_symbol = st.sidebar.selectbox("Choose Symbol", SYMBOLS, index=1)
else:
    player2 = "🤖 Bot"
    st.sidebar.markdown(f"#### Bot Symbol: {st.session_state.bot_symbol}")
    st.session_state.player2_symbol = st.session_state.bot_symbol

# --- Game Logic ---
def check_winner(board):
    lines = board + list(zip(*board))  # rows + columns
    lines += [[board[i][i] for i in range(BOARD_SIZE)], [board[i][BOARD_SIZE - i - 1] for i in range(BOARD_SIZE)]]
    for line in lines:
        if line.count(line[0]) == BOARD_SIZE and line[0] != "":
            return line[0]
    return None

def make_move(row, col, symbol, player):
    if st.session_state.board[row][col] == "" and not st.session_state.game_over:
        st.session_state.board[row][col] = symbol
        st.session_state.moves.append(f"{player} placed {symbol} at ({row+1},{col+1})")
        winner = check_winner(st.session_state.board)
        if winner:
            st.session_state.results.append(f"{player} wins!")
            st.session_state.game_over = True
        elif all(cell != "" for row in st.session_state.board for cell in row):
            st.session_state.results.append("It's a draw!")
            st.session_state.game_over = True

def bot_move():
    empty = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if st.session_state.board[r][c] == ""]
    if empty:
        row, col = random.choice(empty)
        make_move(row, col, st.session_state.bot_symbol, "🤖 Bot")

# --- Main Game UI ---
st.title("🧒 Tic Tac Toe for Kids")
turn = len(st.session_state.moves) % 2
current_player = player1 if turn == 0 else player2
current_symbol = st.session_state.player1_symbol if turn == 0 else st.session_state.player2_symbol

st.subheader(f"Current Turn: {current_player} {current_symbol}")

for r in range(BOARD_SIZE):
    cols = st.columns(BOARD_SIZE)
    for c in range(BOARD_SIZE):
        with cols[c]:
            label = st.session_state.board[r][c]
            if label == "":
                if st.button(" ", key=f"{r}-{c}"):
                    make_move(r, c, current_symbol, current_player)
                    if mode == "1 Player vs Bot" and not st.session_state.game_over:
                        bot_move()
            else:
                st.markdown(f"## {label}")

# --- Show Result Immediately ---
if st.session_state.game_over:
    result = st.session_state.results[-1]
    st.markdown("### 🎉 Game Over!")
    st.success(result)
    if "wins" in result:
        st.balloons()
    else:
        st.snow()

# --- Game Controls ---
st.markdown("🤖" * 10)
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Reset Game"):
        st.session_state.board = [["" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        st.session_state.moves = []
        st.session_state.game_over = False

with col2:
    st.markdown("### 📊 Game Results")
    for i, result in enumerate(st.session_state.results, 1):
        st.write(f"Game {i}: {result}")

with col3:
    st.markdown("### 🕵️ Move History")
    for move in st.session_state.moves:
        st.write(move)
