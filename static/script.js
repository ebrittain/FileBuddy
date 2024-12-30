let currentPath = '';
let firstLoad = true; // Track if it's the first load

// Function to fetch the directory tree and display it
function fetchDirectoryTree() {
    const treeContainer = document.getElementById('file-tree');

    if (!firstLoad) {
        // Start transition: Reduce opacity to 0.5
        treeContainer.style.opacity = 0.5;
    }

    // Wait for the fade-out transition, then load new content
    setTimeout(() => {
        fetch(`/files?path=${currentPath}`)
            .then(response => response.json())
            .then(data => {
                treeContainer.innerHTML = '';
                displayTree(data, treeContainer);

                // Smoothly transition to full opacity
                treeContainer.style.opacity = 1;

                // Set firstLoad to false after the initial load
                firstLoad = false;
            });
    }, firstLoad ? 0 : 300); // Skip delay on the first load
}

// Function to display the directory tree
function displayTree(tree, container) {
    const ul = document.createElement('ul');

    if (currentPath !== '') {
        const previousLi = document.createElement('li');
        previousLi.classList.add('previous');
        const icon = document.createElement('span');
        icon.classList.add('icon');
        icon.textContent = '⬅️';
        previousLi.appendChild(icon);
        previousLi.appendChild(document.createTextNode(' ..'));
        previousLi.onclick = () => {
            currentPath = currentPath.substring(0, currentPath.lastIndexOf('/')) || '';
            fetchDirectoryTree();
        };
        ul.appendChild(previousLi);
    }

    tree.forEach(item => {
        const li = document.createElement('li');
        const icon = document.createElement('span');
        icon.classList.add('icon');

        if (item.type === 'directory') {
            let clickTimeout;

            li.classList.add('directory');
            icon.textContent = '📂';
            li.appendChild(icon);
            li.appendChild(document.createTextNode(item.name));
            li.addEventListener('click', () => {
                clearTimeout(clickTimeout);
                clickTimeout = setTimeout(() => {
                    currentPath = item.path;
                    fetchDirectoryTree();
                }, 300);
            });

            // Double Click: Download Directory
            li.addEventListener('dblclick', () => {
                clearTimeout(clickTimeout);
                downloadDirectory(li, item.path);
            });
        } else {
            li.classList.add('file');
            icon.textContent = '📄';
            li.appendChild(icon);
            li.appendChild(document.createTextNode(item.name));
            li.onclick = () => downloadFile(li, item.name);
        }

        ul.appendChild(li);
    });
    container.appendChild(ul);
}

// Function to download a file with animation
function downloadFile(li, filename) {
    const link = document.createElement('a');
    link.href = `/download/${filename}?directory=${currentPath}`;
    link.download = filename;
    link.click();

    // Show animation
    const animation = document.createElement('span');
    animation.textContent = '✔️ Downloaded';
    animation.classList.add('download-animation');
    li.appendChild(animation);

    // Remove animation after it's done
    setTimeout(() => {
        li.removeChild(animation);
    }, 2500);
}

function downloadDirectory(li, path) {
    const link = document.createElement('a');
    link.href = `/download-directory?path=${path}`;
    link.download = `${path.split('/').pop()}.zip`;
    link.click();

    // Show animation
    const animation = document.createElement('span');
    animation.textContent = '✔️ Downloaded';
    animation.classList.add('download-animation');
    li.appendChild(animation);

    // Remove animation after it's done
    setTimeout(() => {
        li.removeChild(animation);
    }, 2500);
}

// Initialize the directory tree when the page loads
window.onload = function() {
    fetchDirectoryTree();
};