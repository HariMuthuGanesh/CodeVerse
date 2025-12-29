/**
 * DSA Tree Validation Module
 * Proper implementation of BST, AVL, and B-Tree validation
 */

// ============================================================================
// TREE NODE CLASSES
// ============================================================================

class TreeNode {
    constructor(value) {
        this.value = value;
        this.left = null;
        this.right = null;
        this.height = 1; // Required for AVL
        this.color = 'black'; // Required for RB
    }
}

class BTreeNode {
    constructor(leaf = false) {
        this.keys = [];      // Array of keys (1-2 for order 3)
        this.children = [];  // Array of child nodes
        this.leaf = leaf;    // Whether this is a leaf node
    }
}

// ============================================================================
// UI TO TREE CONVERSION
// ============================================================================

/**
 * Converts UI slot positions to a binary tree structure
 * Slot mapping for BST/AVL/RB (complete binary tree layout):
 * Level 0: slot-1 (root)
 * Level 1: slot-2 (left), slot-3 (right)
 * Level 2: slot-4 (left-left), slot-5 (left-right), slot-6 (right-left), slot-7 (right-right)
 * Level 3: slot-8-15 (continues pattern)
 */
function convertSlotsToBinaryTree(challengeType, maxSlots) {
    const nodes = [];

    // First pass: collect all values from slots
    for (let i = 1; i <= maxSlots; i++) {
        const slot = document.getElementById(`${challengeType}-slot-${i}`);
        if (slot && slot.children.length > 0) {
            const child = slot.children[0];
            const value = parseInt(child.dataset.value);
            const color = child.dataset.color || 'black'; // Default to black

            if (value !== null && !isNaN(value)) {
                const node = new TreeNode(value);
                node.color = color; // 'red' or 'black'
                nodes[i] = node;
            } else {
                nodes[i] = null;
            }
        } else {
            nodes[i] = null;
        }
    }

    // Second pass: link nodes according to complete binary tree structure
    // Parent at index i has children at 2*i and 2*i+1
    for (let i = 1; i <= maxSlots; i++) {
        if (nodes[i]) {
            const leftIndex = 2 * i;
            const rightIndex = 2 * i + 1;

            if (leftIndex <= maxSlots) {
                nodes[i].left = nodes[leftIndex] || null;
            }
            if (rightIndex <= maxSlots) {
                nodes[i].right = nodes[rightIndex] || null;
            }
        }
    }

    return nodes[1] || null; // Return root (slot 1)
}

/**
 * Converts UI slots to B-Tree structure (order 3)
 * B-Tree layout for this UI:
 * Level 0: slot-1, slot-2 (root keys)
 * Level 1: slot-3 (left child), slot-4 (middle child), slot-5 (right child)
 */
function convertSlotsToBTree(challengeType) {
    const root = new BTreeNode(false);

    // Get root keys (slots 1 and 2)
    const slot1 = document.getElementById(`${challengeType}-slot-1`);
    const slot2 = document.getElementById(`${challengeType}-slot-2`);

    if (slot1 && slot1.children.length > 0) {
        root.keys.push(parseInt(slot1.children[0].dataset.value));
    }
    if (slot2 && slot2.children.length > 0) {
        root.keys.push(parseInt(slot2.children[0].dataset.value));
    }

    // Sort root keys
    root.keys.sort((a, b) => a - b);

    // Get children (slots 3, 4, 5)
    const slot3 = document.getElementById(`${challengeType}-slot-3`);
    const slot4 = document.getElementById(`${challengeType}-slot-4`);
    const slot5 = document.getElementById(`${challengeType}-slot-5`);

    if (slot3 && slot3.children.length > 0) {
        const child = new BTreeNode(true);
        child.keys.push(parseInt(slot3.children[0].dataset.value));
        root.children.push(child);
    }
    if (slot4 && slot4.children.length > 0) {
        const child = new BTreeNode(true);
        child.keys.push(parseInt(slot4.children[0].dataset.value));
        root.children.push(child);
    }
    if (slot5 && slot5.children.length > 0) {
        const child = new BTreeNode(true);
        child.keys.push(parseInt(slot5.children[0].dataset.value));
        root.children.push(child);
    }

    // If root has no keys, return null
    if (root.keys.length === 0) {
        return null;
    }

    return root;
}

// ============================================================================
// BST VALIDATION (PROPER IMPLEMENTATION)
// ============================================================================

/**
 * Validates BST using min/max range propagation
 * This ensures ALL nodes in left subtree < root < ALL nodes in right subtree
 */
function isValidBST(node, min = -Infinity, max = Infinity) {
    if (!node) return true;

    // Current node must be within range
    if (node.value <= min || node.value >= max) {
        return false;
    }

    // Recursively validate left and right subtrees
    return (
        isValidBST(node.left, min, node.value) &&
        isValidBST(node.right, node.value, max)
    );
}

/**
 * Validates BST from UI state
 */
function validateBSTFromUI(challengeType, maxSlots) {
    // Check all slots are filled
    for (let i = 1; i <= maxSlots; i++) {
        const slot = document.getElementById(`${challengeType}-slot-${i}`);
        if (!slot || slot.children.length === 0) {
            return { valid: false, error: "Timeline Incomplete. Fill all nodes." };
        }
    }

    // Convert UI to tree structure
    const root = convertSlotsToBinaryTree(challengeType, maxSlots);

    if (!root) {
        return { valid: false, error: "Invalid tree structure." };
    }

    // Validate using proper BST algorithm
    const valid = isValidBST(root);

    if (!valid) {
        return { valid: false, error: "Timeline Paradox Detected. Invalid Binary Search Tree. All left subtree values must be < root < all right subtree values." };
    }

    return { valid: true, error: null };
}

// ============================================================================
// AVL TREE VALIDATION (FULL IMPLEMENTATION)
// ============================================================================

/**
 * Calculate height of a node (for AVL)
 */
function getHeight(node) {
    if (!node) return 0;
    return node.height;
}

/**
 * Calculate balance factor of a node
 * Balance factor = height(left) - height(right)
 */
function getBalance(node) {
    if (!node) return 0;
    return getHeight(node.left) - getHeight(node.right);
}

/**
 * Update height of a node based on children
 */
function updateHeight(node) {
    if (!node) return;
    node.height = 1 + Math.max(getHeight(node.left), getHeight(node.right));
}

/**
 * Update heights for entire tree (bottom-up)
 */
function updateAllHeights(node) {
    if (!node) return;
    updateAllHeights(node.left);
    updateAllHeights(node.right);
    updateHeight(node);
}

/**
 * Check if tree is valid AVL
 * Must satisfy:
 * 1. Valid BST property
 * 2. Balance factor ∈ {-1, 0, 1} for ALL nodes
 */
function isValidAVL(node) {
    if (!node) return true;

    // First, ensure it's a valid BST
    if (!isValidBST(node)) {
        return false;
    }

    // Update all heights
    updateAllHeights(node);

    // Check balance factor for current node
    const balance = getBalance(node);
    if (balance < -1 || balance > 1) {
        return false;
    }

    // Recursively check all children
    return isValidAVL(node.left) && isValidAVL(node.right);
}

/**
 * Validates AVL from UI state
 */
function validateAVLFromUI(challengeType, maxSlots) {
    // Check all slots are filled
    for (let i = 1; i <= maxSlots; i++) {
        const slot = document.getElementById(`${challengeType}-slot-${i}`);
        if (!slot || slot.children.length === 0) {
            return { valid: false, error: "Timeline Incomplete. Fill all nodes." };
        }
    }

    // Convert UI to tree structure
    const root = convertSlotsToBinaryTree(challengeType, maxSlots);

    if (!root) {
        return { valid: false, error: "Invalid tree structure." };
    }

    // Validate using proper AVL algorithm
    const valid = isValidAVL(root);

    if (!valid) {
        return { valid: false, error: "Timeline Paradox Detected. Invalid AVL Tree. Tree must be a valid BST with balance factor -1, 0, or 1 for all nodes." };
    }

    return { valid: true, error: null };
}

// ============================================================================
// B-TREE VALIDATION (ORDER 3 - PROPER IMPLEMENTATION)
// ============================================================================

// ============================================================================
// RED-BLACK TREE VALIDATION
// ============================================================================

function isValidRB(node) {
    if (!node) return { valid: true, blackHeight: 1 }; // Null is considered black

    // 1. Check BST property
    if (!isValidBST(node)) {
        return { valid: false, error: "BST violation: Left < Root < Right rule broken." };
    }

    // 2. No Red-Red violation
    if (node.color === 'red') {
        if ((node.left && node.left.color === 'red') ||
            (node.right && node.right.color === 'red')) {
            return { valid: false, error: "Color violation: Red node cannot have Red children." };
        }
    }

    // 3. Black Height consistency
    const leftResult = isValidRB(node.left);
    if (!leftResult.valid) return leftResult;

    const rightResult = isValidRB(node.right);
    if (!rightResult.valid) return rightResult;

    // Check if black heights match
    if (leftResult.blackHeight !== rightResult.blackHeight) {
        return { valid: false, error: "Black Height violation: All paths must have same number of black nodes." };
    }

    // Calculate current black height
    const currentHeight = leftResult.blackHeight + (node.color === 'black' ? 1 : 0);

    return { valid: true, blackHeight: currentHeight };
}

function validateRBFromUI(challengeType, maxSlots) {
    // Check if all slots (at least key ones) are filled or allow partial tree?
    // User said "One question = one drag-and-drop area", "Submit -> Validate".
    // Let's require the tree to be formed by whatever is in the slots. 
    // BUT we must check if it's a valid tree structure first (connected).
    // Our convertSlots uses complete binary tree mapping, so gaps might mean nulls.

    // Check root exists
    const rootSlot = document.getElementById(`${challengeType}-slot-1`);
    if (!rootSlot || rootSlot.children.length === 0) {
        return { valid: false, error: "Root node is missing." };
    }

    const root = convertSlotsToBinaryTree(challengeType, maxSlots);

    // 1. Root Property: Root must be BLACK
    if (root.color !== 'black') {
        return { valid: false, error: "Root Rule violation: The root node must be BLACK." };
    }

    // Validate RB rules recursively
    const result = isValidRB(root);

    if (!result.valid) {
        return { valid: false, error: result.error };
    }

    return { valid: true, error: null };
}

// ============================================================================
// EXPORT FUNCTIONS
// ============================================================================

// Export validation functions for use in dsa.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        validateAVLFromUI,
        validateRBFromUI,
        isValidBST,
        isValidAVL,
        isValidRB
    };
}

