/**
 * DSA Tree Logic Module
 * Handles Node structures and Validation logic
 */

class TreeNode {
    constructor(value) {
        this.value = value;
        this.left = null;
        this.right = null;
        this.color = 'black'; // RB Support
        this.highlight = false; // Viz support
    }
}

// Visualizer: Draw Tree to DOM
// Simplistic recursive DOM renderer for the BST Visualization
function renderTreeToDOM(root, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '';
    if (!root) {
        container.innerHTML = '<div style="position:absolute; top:50%; color:gray;">Empty Tree</div>';
        return;
    }

    const treeEl = createTreeDOMRecursive(root);
    container.appendChild(treeEl);
}

function createTreeDOMRecursive(node) {
    if (!node) return document.createElement('div'); // spacer

    const wrapper = document.createElement('div');
    wrapper.className = 'tree-node';

    const circle = document.createElement('div');
    circle.className = `node-circle ${node.highlight ? 'highlight' : ''}`;
    circle.textContent = node.value;
    if (node.color === 'red') {
        circle.style.background = '#D00';
        circle.style.border = '2px solid white';
    } else if (node.color === 'black') {
        circle.style.background = 'black';
        circle.style.border = '2px solid var(--accent-avengers)';
    } else {
        // Standard BST node
        circle.style.background = 'var(--accent-avengers)';
    }

    wrapper.appendChild(circle);

    if (node.left || node.right) {
        const childrenContainer = document.createElement('div');
        childrenContainer.style.display = 'flex';
        childrenContainer.style.marginTop = '20px';
        childrenContainer.style.gap = '20px';
        childrenContainer.style.borderTop = '2px solid rgba(255,255,255,0.2)'; // Simple connector line

        childrenContainer.appendChild(createTreeDOMRecursive(node.left));
        childrenContainer.appendChild(createTreeDOMRecursive(node.right));

        wrapper.appendChild(childrenContainer);
    }

    return wrapper;
}

// --- UTILS ---

function insertBST(root, value) {
    if (!root) return new TreeNode(value);
    if (value < root.value) root.left = insertBST(root.left, value);
    else if (value > root.value) root.right = insertBST(root.right, value);
    return root;
}

function searchBST(root, value) {
    if (!root || root.value == value) return root;
    if (value < root.value) return searchBST(root.left, value);
    return searchBST(root.right, value);
}

function getMin(node) {
    while (node.left) node = node.left;
    return node;
}

function deleteBST(root, value) {
    if (!root) return root;

    if (value < root.value) root.left = deleteBST(root.left, value);
    else if (value > root.value) root.right = deleteBST(root.right, value);
    else {
        // Node found
        if (!root.left) return root.right;
        if (!root.right) return root.left;

        let temp = getMin(root.right);
        root.value = temp.value;
        root.right = deleteBST(root.right, temp.value);
    }
    return root;
}

function inorderBST(root, res = []) {
    if (!root) return res;
    inorderBST(root.left, res);
    res.push(root.value);
    inorderBST(root.right, res);
    return res;
}


// --- VALIDATION (Legacy/RB) ---

function isValidBST(node, min = -Infinity, max = Infinity) {
    if (!node) return true;
    if (node.value <= min || node.value >= max) return false;
    return isValidBST(node.left, min, node.value) && isValidBST(node.right, node.value, max);
}

function isValidRB(node) {
    if (!node) return { valid: true, blackHeight: 1 };

    if (!isValidBST(node)) return { valid: false, error: "Not a BST" };

    if (node.color === 'red') {
        if ((node.left && node.left.color === 'red') || (node.right && node.right.color === 'red')) {
            return { valid: false, error: "Red node has Red child" };
        }
    }

    const l = isValidRB(node.left);
    if (!l.valid) return l;
    const r = isValidRB(node.right);
    if (!r.valid) return r;

    if (l.blackHeight !== r.blackHeight) return { valid: false, error: "Black height mismatch" };

    return { valid: true, blackHeight: l.blackHeight + (node.color === 'black' ? 1 : 0) };
}

// Helper to convert slots back to tree (for RB legacy challenge)
function convertSlotsToTree(prefix, count) {
    // Array rep 1-based
    let nodes = new Array(count + 1).fill(null);

    for (let i = 1; i <= count; i++) {
        const slot = document.getElementById(`${prefix}-slot-${i}`);
        if (slot && slot.children.length > 0) {
            const el = slot.children[0];
            const val = parseInt(el.dataset.value);
            const col = el.dataset.color || 'black';
            const n = new TreeNode(val);
            n.color = col;
            nodes[i] = n;
        }
    }

    // Link
    for (let i = 1; i <= count; i++) {
        if (nodes[i]) {
            if (2 * i <= count) nodes[i].left = nodes[2 * i];
            if (2 * i + 1 <= count) nodes[i].right = nodes[2 * i + 1];
        }
    }

    return nodes[1];
}

function validateRBFromUI() {
    // Check Root
    const root = convertSlotsToTree('rb', 7);
    if (!root) return { valid: false, error: "Root missing" };
    if (root.color !== 'black') return { valid: false, error: "Root must be black" };
    return isValidRB(root);
}

// Export for usage if needed (though we just load script globally)
if (typeof window !== 'undefined') {
    window.DSATree = {
        TreeNode,
        insertBST,
        searchBST,
        deleteBST,
        inorderBST,
        renderTreeToDOM,
        validateRBFromUI
    };
}
