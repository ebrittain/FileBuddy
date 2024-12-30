# FileBuddy

FileBuddy is a user-friendly and secure file server application that allows users to browse, navigate, and download files from a directory structure via a sleek web interface. It supports downloading entire directories as `.zip` files and includes a password-protected interface for enhanced security.

## Features

- **Secure Access**: Password-protected interface to restrict unauthorized access.
- **Directory Navigation**: Navigate through folders in a visually intuitive tree view.
- **File Downloads**: Download individual files with a single click.
- **Directory Downloads**: Download entire directories as `.zip` files by double-clicking.
- **Responsive Design**: Optimized for both desktop and mobile devices.
- **Cross-Platform Compatibility**: Works seamlessly on Windows, macOS, and Linux.

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python with Flask
- **Deployment**: Docker support for simplified deployment

## Installation

### Prerequisites

- Python 3.x installed
- Flask library (`pip install flask`)

### Steps

1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/filebuddy.git
    cd filebuddy
    ```
2. Start the Flask server
    ```bash
    python server.py --base-dir /path/to/files --password yourpassword
    ```
3. Access the application in your browser:
    ```plaintext
    http://127.0.0.1:5000
    ```

