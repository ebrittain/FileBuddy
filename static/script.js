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
            li.onclick = () => downloadFile(item.name, li);
        }

        ul.appendChild(li);
    });
    container.appendChild(ul);
}

// Function to download a file with animation
function downloadFile(filename, li = null) {
    const link = document.createElement('a');
    link.href = `/download/${filename}?directory=${currentPath}`;
    link.download = filename;
    link.click();

    // Show animation
    if (li != null) {
        const animation = document.createElement('span');
        animation.textContent = '✔️ Downloaded';
        animation.classList.add('download-animation');
        li.appendChild(animation);

        // Remove animation after it's done
        setTimeout(() => {
            li.removeChild(animation);
        }, 2500);
    }
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

/**
 * Performs a search and displays recommendations based on user input.
 * @param {string} query - The search query.
 */
async function searchFiles(query) {
    if (!query.trim()) {
        return; // Ignore empty queries
    }

    try {
        const response = await fetch(`/search?query=${encodeURIComponent(query)}&path=${encodeURIComponent(currentPath)}`);
        if (!response.ok) throw new Error(`Search failed: ${response.statusText}`);

        const results = await response.json();
        displaySearchResults(results);
    } catch (error) {
        console.error("Error performing search:", error);
    }
}

/**
 * Displays search results as recommendations.
 * @param {Array} results - List of matching files and directories.
 */
function displaySearchResults(results) {
    const searchResultsContainer = document.getElementById("search-results");
    const searchBar = document.getElementById("search-bar");
    searchResultsContainer.innerHTML = ''; // Clear previous results

    results.forEach((item) => {
        const resultItem = document.createElement('div');
        resultItem.classList.add('search-result');
        resultItem.textContent = `${item.type === 'directory' ? '📂' : '📄'} ${item.relative_path}`;
        resultItem.addEventListener('click', () => {
            if (item.type === 'directory') {
                currentPath = item.relative_path
                fetchDirectoryTree();
            } else {
                currentPath = item.relative_path.substring(0, item.relative_path.lastIndexOf('/')) || '';
                downloadFile(item.name);
            }
            searchResultsContainer.innerHTML = '';
            searchBar.value = '';
        });

        searchResultsContainer.appendChild(resultItem);
    });
}

// Add search bar input handler
document.getElementById("search-bar").addEventListener("input", (event) => {
    const query = event.target.value;
    searchFiles(query);
});


// Initialize the directory tree when the page loads
window.onload = function() {
    fetchDirectoryTree();
};