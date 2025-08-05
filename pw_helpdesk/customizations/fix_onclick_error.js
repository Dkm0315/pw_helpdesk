/**
 * Fix for CustomActions.vue onClick error
 * This script can be included to prevent "l.onClick is not a function" errors
 */

// Monkey patch for CustomActions to handle missing onClick functions
(function() {
    // Wait for Vue to be available
    if (typeof window !== 'undefined' && window.Vue) {
        
        // Override the CustomActions component's action handler
        function patchCustomActions() {
            // Create a safer onClick handler
            function safeOnClick(action) {
                if (action && typeof action.onClick === 'function') {
                    try {
                        return action.onClick();
                    } catch (error) {
                        console.error('Error executing action onClick:', error);
                        frappe.msgprint('Action could not be completed. Please try again.');
                    }
                } else {
                    console.warn('Action missing onClick function:', action);
                    frappe.msgprint('This action is not properly configured.');
                }
            }
            
            // Patch the click handler in any CustomActions components
            const originalComponents = window.Vue.options.components;
            if (originalComponents && originalComponents.CustomActions) {
                const original = originalComponents.CustomActions;
                
                // Create a patched version
                const patched = {
                    ...original,
                    methods: {
                        ...original.methods,
                        handleActionClick(action) {
                            return safeOnClick(action);
                        }
                    }
                };
                
                window.Vue.options.components.CustomActions = patched;
                console.log('✅ CustomActions onClick error fix applied');
            }
        }
        
        // Apply the patch when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', patchCustomActions);
        } else {
            patchCustomActions();
        }
        
    } else {
        // Retry when Vue becomes available
        setTimeout(arguments.callee, 100);
    }
})();

// Also provide a global safe action executor
window.pw_helpdesk_safe_action = function(action) {
    if (action && typeof action.onClick === 'function') {
        try {
            return action.onClick();
        } catch (error) {
            console.error('Error executing action:', error);
            if (window.frappe && frappe.msgprint) {
                frappe.msgprint('Action could not be completed. Please try again.');
            }
        }
    } else {
        console.warn('Invalid action provided:', action);
        if (window.frappe && frappe.msgprint) {
            frappe.msgprint('This action is not properly configured.');
        }
    }
};

// Enhanced form script validation for HD Ticket actions
window.validateTicketActions = function(actions) {
    if (!Array.isArray(actions)) {
        return [];
    }
    
    return actions.map(action => {
        if (typeof action !== 'object' || !action) {
            return null;
        }
        
        // Ensure required properties
        if (!action.label) {
            console.warn('Action missing label:', action);
            return null;
        }
        
        // Ensure onClick is a function
        if (typeof action.onClick !== 'function') {
            console.warn('Action missing onClick function:', action);
            action.onClick = function() {
                console.warn('No onClick handler for action:', action.label);
                if (window.frappe && frappe.msgprint) {
                    frappe.msgprint(`Action "${action.label}" is not properly configured.`);
                }
            };
        }
        
        // Wrap onClick in error handler
        const originalOnClick = action.onClick;
        action.onClick = function() {
            try {
                return originalOnClick.apply(this, arguments);
            } catch (error) {
                console.error('Error in action onClick:', error);
                if (window.frappe && frappe.msgprint) {
                    frappe.msgprint('Action could not be completed. Please try again.');
                }
            }
        };
        
        return action;
    }).filter(action => action !== null);
};

console.log('🔧 PW Helpdesk onClick error fixes loaded'); 