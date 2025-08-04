frappe.ui.form.on('HD Service Level Agreement', {
    refresh: function(frm) {
        // Real-time condition preview
        if (frm.doc.custom_applicable_categories && frm.doc.custom_applicable_categories.length > 0) {
            show_condition_preview(frm);
        }
    },
    
    custom_auto_assign_team: function(frm) {
        // Auto-set assignment rule when team is selected
        if (frm.doc.custom_auto_assign_team && !frm.doc.custom_assignment_rule) {
            frappe.db.get_value('HD Team', frm.doc.custom_auto_assign_team, 'assignment_rule')
                .then(r => {
                    if (r.message.assignment_rule) {
                        frm.set_value('custom_assignment_rule', r.message.assignment_rule);
                        frappe.show_alert({
                            message: __('Assignment rule auto-set from team: {0}', [r.message.assignment_rule]),
                            indicator: 'blue'
                        });
                    }
                });
        }
    },
    
    // Real-time validation on save
    before_save: function(frm) {
        // Let server-side validation handle condition generation
        // This ensures consistent behavior
    }
});

frappe.ui.form.on('HD Category Selection', {
    category_add: function(frm, cdt, cdn) {
        // Show real-time condition preview
        setTimeout(() => show_condition_preview(frm), 100);
    },
    
    category_remove: function(frm, cdt, cdn) {
        // Show real-time condition preview
        setTimeout(() => show_condition_preview(frm), 100);
    },
    
    category: function(frm, cdt, cdn) {
        // Show real-time condition preview
        setTimeout(() => show_condition_preview(frm), 100);
    }
});

function show_condition_preview(frm) {
    // Get selected categories
    let categories = [];
    if (frm.doc.custom_applicable_categories) {
        frm.doc.custom_applicable_categories.forEach(function(row) {
            if (row.category) {
                categories.push(row.category);
            }
        });
    }
    
    if (categories.length === 0) {
        // Clear any existing preview
        frm.dashboard.clear_comment();
        return;
    }
    
    // Generate condition preview
    let condition = '';
    if (categories.length === 1) {
        condition = `doc.custom_category == '${categories[0]}'`;
    } else {
        let category_list = categories.map(cat => `'${cat}'`).join(', ');
        condition = `doc.custom_category in [${category_list}]`;
    }
    
    // Show condition preview in dashboard
    frm.dashboard.clear_comment();
    frm.dashboard.add_comment(
        __('Condition Preview: {0}', [condition]), 
        'blue', 
        true
    );
    
    // Show real-time alert
    frappe.show_alert({
        message: __('Condition will be: {0}', [condition]),
        indicator: 'blue'
    });
} 