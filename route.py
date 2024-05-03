import subprocess
import time
import threading

def get_connected_clients():
    try:
        # Run jack_lsp to list connected clients and their connections
        result = subprocess.run(["jack_lsp", "-c"], capture_output=True, text=True)
        
        # # Print the output
        # print("Output:", result.stdout)
        # # Print any errors
        # print("Errors:", result.stderr)
        
        lines = result.stdout.strip().split('\n')

        # Extract client names (lines without indentation)
        clients = [line.strip() for line in lines if (not line.startswith(' ') and not line.startswith('system'))]
        # print("Clients:", clients)
        return clients
    except Exception as e:
        print('Critical Error: ', e)
        return e


def detect_new_clients(previous_clients):
    # Get the current list of connected clients
    current_clients = get_connected_clients()

    # Compare with the previous list to detect changes
    new_clients = [client for client in current_clients if client not in previous_clients]

    return new_clients


def get_connected_ports():
    # Run jack_lsp command with the -c flag to list connected ports
    result = subprocess.run(["jack_lsp", "-c"], capture_output=True, text=True)

    # Parse the output to identify connected ports
    connected_ports_capture = {}
    connected_ports_playback = {}


    current_port = None
    for line in result.stdout.strip().split('\n'):
        if line:
            if line.startswith(' '):
                # This line contains connection information
                if current_port.startswith('system:capture'):
                    connected_ports_capture[current_port] = line.strip()
                elif current_port.startswith('system:playback'):
                    connected_ports_playback[current_port] = line.strip()
            else:
                # This line contains a port name
                current_port = line
    return connected_ports_capture, connected_ports_playback


def run():
    previous_clients = get_connected_clients()
    while True:

        new_clients = detect_new_clients(previous_clients)
        if new_clients:

            # Disconnect existing port connections for new client
            for client in new_clients:

                if 'send' in client:
                    try:
                        subprocess.run(["jack_disconnect", 'system:capture_{}'.format(client[-1]), client], check=True)
                        print(f"Disconnected {'system:capture_{}'.format(client[-1])} and {client}")
                    except subprocess.CalledProcessError as e:
                        print(f"Error disconnecting ports: {e}")
                else:
                    try:
                        subprocess.run(["jack_disconnect", 'system:playback_{}'.format(client[-1]), client], check=True)
                        print(f"Disconnected {'system:playback_{}'.format(client[-1])} and {client}")
                    except subprocess.CalledProcessError as e:
                        print(f"Error disconnecting ports: {e}")

            connected_ports_capture, connected_ports_playback = get_connected_ports()

            # Establish new port connections
            for client in new_clients:

                i = 1
                notFound = True
                while notFound:
                    if not ('system:playback_{}'.format(i) in connected_ports_playback):
                        notFound = False
                    elif i > 50: #Change this dynamically
                        print(connected_ports_playback)
                        break
                    else:
                        i = i + 1

                if 'send_2' in client:
                    try:
                        subprocess.run(["jack_connect", 'system:capture_{}'.format(i+4), client], check=True)
                        print(f"Connected {'system:capture_{}'.format(i+4)} and {client}")
                    except subprocess.CalledProcessError as e:
                        print(f"Error connecting ports: {e}")
                elif 'receive_1' in client:
                    try:
                        subprocess.run(["jack_connect", 'system:playback_{}'.format(i), client], check=True)
                        print(f"Connected {'system:playback_{}'.format(i)} and {client}")
                    except subprocess.CalledProcessError as e:
                        print(f"Error connecting ports: {e}")

        previous_clients = get_connected_clients()
        time.sleep(1)  # Adjust the sleep time as needed

        connected_ports_capture, connected_ports_playback = get_connected_ports()
        print(connected_ports_playback)

def main():
    """Sets up threading and runs the connection manager."""
    connection_thread = threading.Thread(target=run)
    connection_thread.daemon = True
    connection_thread.start()
 
    try:
        while True:
            time.sleep(10)  # Main thread waits or performs other tasks
    except KeyboardInterrupt:
        print("Stopping...")
 
if __name__ == "__main__":
    main()