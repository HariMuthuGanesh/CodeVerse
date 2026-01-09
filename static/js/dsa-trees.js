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


// 2. RB VALIDATOR (New Fixed UI)
function validateRBFromUI() {
    const root = convertFixedRBToTree();
    if (!root) return { valid: false, error: "Root missing" };

    // Check Root Color
    if (root.color !== 'black') return { valid: false, error: "Root must be BLACK." };

    return isValidRB(root);
}

function isValidRB(node) {
    if (!node) return { valid: true, blackHeight: 1 };

    // Red Violation Check
    if (node.color === 'red') { // Check Red-Red
        if ((node.left && node.left.color === 'red') ||
            (node.right && node.right.color === 'red')) {
            return { valid: false, error: `Red Constraint Violated at Node ${node.value} (Red parent cannot have Red child)` };
        }
    }

    const l = isValidRB(node.left);
    if (!l.valid) return l;
    const r = isValidRB(node.right);
    if (!r.valid) return r;

    // Black Height Check
    if (l.blackHeight !== r.blackHeight) {
        return {
            valid: false,
            error: `Black Height Violation at Node ${node.value} (Left: ${l.blackHeight}, Right: ${r.blackHeight})`
        };
    }

    // Determine current black height contribution
    // Note: Standard definition counts black nodes on path.
    // Null counts as black (height 1 returned above).
    // If current is black, add 1. If red, add 0.
    // Wait, if null returns 1 (representing a black leaf/nil), then:
    // Leaf node (Black) -> L(1), R(1) -> Returns 1 + 1 = 2?
    // Let's stick to standard: Count number of black nodes from node to leaf.
    // Null is black.

    // Correct logic:
    // If I am black, my height is child_bh + 1.
    // If I am red, my height is child_bh.

    return {
        valid: true,
        blackHeight: l.blackHeight + (node.color === 'black' ? 1 : 0)
    };
}

// --- UTILS ---

function getSlotValue(prefix, index) {
    const slot = document.getElementById(`${prefix}-slot-${index}`);
    if (slot && slot.children.length > 0) {
        return parseInt(slot.children[0].dataset.value);
    }
    return null;
}

function convertFixedRBToTree() {
    // Fixed Structure: 1-7
    // 1 -> 2, 3
    // 2 -> 4, 5
    // 3 -> 6, 7

    const getNode = (id) => {
        const el = document.getElementById(`rb-node-${id}`);
        if (!el) return null;
        const val = parseInt(el.dataset.value);
        // color from style or default?
        // Note: style.backgroundColor returns 'black', '#AA0000', 'rgb(...)', or ''
        const bg = el.style.backgroundColor;
        const color = (bg === 'black' || bg === '' || bg === 'rgb(0, 0, 0)') ? 'black' : 'red';

        const n = new TreeNode(val);
        n.color = color;
        return n;
    };

    const n1 = getNode(1);
    const n2 = getNode(2);
    const n3 = getNode(3);
    const n4 = getNode(4);
    const n5 = getNode(5);
    const n6 = getNode(6);
    const n7 = getNode(7);

    if (n1) { n1.left = n2; n1.right = n3; }
    if (n2) { n2.left = n4; n2.right = n5; }
    if (n3) { n3.left = n6; n3.right = n7; }

    return n1;
}

function convertSlotsToTree(prefix, count) {
    // Only used for legacy or potentially detective if needed?
    // Detective uses validateBSTFromUI which uses getSlotValue logic manually.
    // So this might be unused, but keeping it safe or removing if unused.
    // Let's keep it but fixing the undefined color issue if any.
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

// 3. TRAVERSAL VALIDATOR
function validateTraversal(attempts) {
    // Reference Tree (Inorder):
    // Tree: 
    //      50
    //    /    \
    //   30    70
    //  /  \  /  \
    // 20 40 60  80
    //
    // Inorder: Left, Root, Right
    // 20, 30, 40, 50, 60, 70, 80
    const correctOrder = [20, 30, 40, 50, 60, 70, 80];

    // attempts is array of values from slot 1 to 7
    if (!attempts || attempts.length !== 7) return { valid: false, error: "Incomplete sequence." };

    for (let i = 0; i < 7; i++) {
        if (attempts[i] !== correctOrder[i]) {
            return { valid: false, error: `Incorrect sequence at position ${i + 1}.` };
        }
    }
    return { valid: true };
}

// 4. LOCAL BST CHECK (For Real-time Shake)
function checkLocalBST(slotIndex, value, currentSlots) {
    // Returns true if valid placement LOCALLY (parent check only)
    // currentSlots is map {slotIndex: value}

    // Root (1) always valid locally
    if (slotIndex === 1) return true;

    const parent = Math.floor(slotIndex / 2);
    const parentVal = currentSlots[parent];

    if (!parentVal) return true; // Parent not present yet, assume valid for now? Or strict?
    // Let's be strict: if parent exists, check.

    const isLeft = (slotIndex % 2 === 0);

    if (isLeft) {
        if (value >= parentVal) return false; // Must be < Parent
    } else {
        if (value <= parentVal) return false; // Must be > Parent
    }

    return true;
}

// Export
if (typeof window !== 'undefined') {
    window.DSATree = {
        TreeNode,
        validateBSTFromUI,
        validateRBFromUI,
        validateTraversal,
        checkLocalBST
    };
}
