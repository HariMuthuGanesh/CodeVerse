/**
 * DSA Tree Logic Module
 * Handles Node structures and Validation logic
 */

class TreeNode {
    constructor(value) {
        this.value = parseInt(value);
        this.left = null;
        this.right = null;
        this.color = 'black'; // RB Support
    }
}

// --- VALIDATION LOGIC ---

// 1. BST VALIDATOR
function validateBSTFromUI(prefix = 'bst') {
    // 1. Build Tree from Slots (1-7)
    // Structure is fixed:
    // Slot 1 (Root) -> 2 (L), 3 (R)
    // Slot 2 -> 4 (L), 5 (R)
    // Slot 3 -> 6 (L), 7 (R)

    // Check if empty
    const nodes = new Array(8).fill(null); // 1-indexed for convenience
    let count = 0;

    for (let i = 1; i <= 7; i++) {
        const el = getSlotValue(prefix, i);
        if (el !== null) {
            nodes[i] = new TreeNode(el);
            count++;
        }
    }

    if (count === 0) return { valid: false, error: "The tree is empty." };
    if (count < 7) return { valid: false, error: "Incomplete Tree. Use all stones." };

    // Link nodes
    // 1 -> 2, 3
    if (nodes[1]) {
        nodes[1].left = nodes[2];
        nodes[1].right = nodes[3];
    }
    // 2 -> 4, 5
    if (nodes[2]) {
        nodes[2].left = nodes[4];
        nodes[2].right = nodes[5];
    }
    // 3 -> 6, 7
    if (nodes[3]) {
        nodes[3].left = nodes[6];
        nodes[3].right = nodes[7];
    }

    // STRICT VALIDATION
    // Must respect Min/Max constraints from ancestors
    return isValidBST(nodes[1], -Infinity, Infinity);
}

function isValidBST(node, min, max) {
    if (!node) return { valid: true };

    if (node.value <= min || node.value >= max) {
        return {
            valid: false,
            error: `Violation: Node ${node.value} must be between ${min === -Infinity ? '-∞' : min} and ${max === Infinity ? '∞' : max}`
        };
    }

    const l = isValidBST(node.left, min, node.value);
    if (!l.valid) return l;

    const r = isValidBST(node.right, node.value, max);
    if (!r.valid) return r;

    return { valid: true };
}


// 2. RB VALIDATOR (Legacy)
function validateRBFromUI() {
    const root = convertSlotsToTree('rb', 7);
    if (!root) return { valid: false, error: "Root missing" };
    if (root.color !== 'black') return { valid: false, error: "Root must be black" };
    return isValidRB(root);
}

function isValidRB(node) {
    if (!node) return { valid: true, blackHeight: 1 };

    // Basic BST Check
    // Reuse specific BST logic or basic check? Let's do basic local check + recursiveness
    if (node.left && node.left.value >= node.value) return { valid: false, error: `Invalid BST Order: ${node.left.value} >= ${node.value}` };
    if (node.right && node.right.value <= node.value) return { valid: false, error: `Invalid BST Order: ${node.right.value} <= ${node.value}` };

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


// --- UTILS ---

function getSlotValue(prefix, index) {
    const slot = document.getElementById(`${prefix}-slot-${index}`);
    if (slot && slot.children.length > 0) {
        return parseInt(slot.children[0].dataset.value);
    }
    return null;
}

function convertSlotsToTree(prefix, count) {
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
    for (let i = 1; i <= count; i++) {
        if (nodes[i]) {
            if (2 * i <= count) nodes[i].left = nodes[2 * i];
            if (2 * i + 1 <= count) nodes[i].right = nodes[2 * i + 1];
        }
    }
    return nodes[1];
}

// Export
if (typeof window !== 'undefined') {
    window.DSATree = {
        TreeNode,
        validateBSTFromUI,
        validateRBFromUI
    };
}
