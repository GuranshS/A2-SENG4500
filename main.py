import socket
import sys
import random

BROADCAST_ADDR = sys.argv[1] if len(sys.argv) > 1 else "255.255.255.255"
BROADCAST_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5000

# Generate a random TCP port between 9000-9100 for player connection
TCP_PORT = random.randint(9000, 9100)

def send_new_game_message():
    """Send a 'NEW GAME' message over UDP."""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    message = f"NEW GAME:{TCP_PORT}".encode('utf-8')
    udp_socket.sendto(message, (BROADCAST_ADDR, BROADCAST_PORT))
    print(f"Sent 'NEW GAME' on UDP port {BROADCAST_PORT} with TCP port {TCP_PORT}")

    udp_socket.close()

def listen_for_new_game():
    """Listen for 'NEW GAME' messages over UDP."""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    udp_socket.bind(('', BROADCAST_PORT))
    udp_socket.settimeout(30)  # Listen for 30 seconds

    try:
        data, addr = udp_socket.recvfrom(1024)
        message = data.decode('utf-8')
        print(f"Received message: {message} from {addr}")

        # Extract the TCP port from the message
        return addr[0], int(message.split(":")[1])
    except socket.timeout:
        print("No 'NEW GAME' message received.")
        return None, None
    finally:
        udp_socket.close()

    
def start_tcp_connection(ip, tcp_port):
    """Connect to the other player via TCP."""
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((ip, tcp_port))
    print(f"Connected to {ip}:{tcp_port} over TCP")
    return tcp_socket

def wait_for_tcp_connection(tcp_port):
    """Wait for the other player to connect via TCP."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', tcp_port))
    server_socket.listen(1)
    print(f"Waiting for connection on TCP port {tcp_port}...")

    conn, addr = server_socket.accept()
    print(f"Connected to {addr}")
    return conn

def print_grid(grid):
    """Print the Connect 4 grid."""
    for row in grid:
        print(' '.join(row))
    print()

def insert_piece(grid, column, piece):
    """Insert a piece into the specified column."""
    for row in reversed(grid):
        if row[column] == '.':
            row[column] = piece
            return True
    return False

def check_win(grid, piece):
    """Check if a player has won."""
    # Horizontal, vertical, and diagonal checks can be implemented here.
    pass

def play_game(connection, is_player1):
    """Play the game by exchanging INSERT messages."""
    grid = [['.' for _ in range(7)] for _ in range(6)]
    player_piece = 'X' if is_player1 else 'O'

    while True:
        print_grid(grid)
        if is_player1:
            column = int(input("Enter the column (0-6): "))
            insert_piece(grid, column, player_piece)
            connection.send(f"INSERT:{column}".encode('utf-8'))
        else:
            data = connection.recv(1024).decode('utf-8')
            if "INSERT" in data:
                column = int(data.split(":")[1])
                insert_piece(grid, column, player_piece)
            elif "YOU WIN" in data:
                print("You lose!")
                break

        # Check for win condition
        if check_win(grid, player_piece):
            print("You win!")
            connection.send(b"YOU WIN")
            break

        # Switch turns
        is_player1 = not is_player1

def main():
    # Step 1: Listen for a new game via UDP
    ip, other_tcp_port = listen_for_new_game()

    if other_tcp_port:
        # If a game is found, connect to the other player via TCP
        connection = start_tcp_connection(ip, other_tcp_port)
        play_game(connection, is_player1=False)
    else:
        # No game found, announce a new game and wait for a connection
        send_new_game_message()
        connection = wait_for_tcp_connection(TCP_PORT)
        play_game(connection, is_player1=True)

if __name__ == "__main__":
    main()

