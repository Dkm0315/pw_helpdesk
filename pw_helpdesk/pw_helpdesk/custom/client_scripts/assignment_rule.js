frappe.ui.form.on('Assignment Rule', {
    refresh: function(frm) {
        // Real-time condition preview
        if (frm.doc.custom_applicable_categories && frm.doc.custom_applicable_categories.length > 0) {
            show_assignment_condition_preview(frm);
        }
        
        // Show warning for non-HD Ticket document types
        if (frm.doc.document_type && frm.doc.document_type !== 'HD Ticket') {
            frm.dashboard.clear_comment();
            frm.dashboard.add_comment(
                __('Category-based assignment only works for HD Ticket document type'), 
                'orange', 
                true
            );
        }
    },
    
    document_type: function(frm) {
        // Clear categories when document type changes
        if (frm.doc.document_type !== 'HD Ticket') {
            frm.clear_table('custom_applicable_categories');
            frm.refresh_field('custom_applicable_categories');
            frm.dashboard.clear_comment();
            frm.dashboard.add_comment(
                __('Category-based assignment only works for HD Ticket document type'), 
                'orange', 
                true
            );
        } else {
            frm.dashboard.clear_comment();
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
        setTimeout(() => show_assignment_condition_preview(frm), 100);
    },
    
    category_remove: function(frm, cdt, cdn) {
        // Show real-time condition preview
        setTimeout(() => show_assignment_condition_preview(frm), 100);
    },
    
    category: function(frm, cdt, cdn) {
        // Show real-time condition preview
        setTimeout(() => show_assignment_condition_preview(frm), 100);
    }
});

function show_assignment_condition_preview(frm) {
    if (frm.doc.document_type !== 'HD Ticket') {
        frm.dashboard.clear_comment();
        frm.dashboard.add_comment(
            __('Category-based assignment only works for HD Ticket document type'), 
            'orange', 
            true
        );
        return;
    }
    
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
    
    // Generate condition preview for assignment rule
    let condition = '';
    if (categories.length === 1) {
        condition = `custom_category == '${categories[0]}'`;
    } else {
        let category_list = categories.map(cat => `'${cat}'`).join(', ');
        condition = `custom_category in [${category_list}]`;
    }
    
    // Show condition preview in dashboard
    frm.dashboard.clear_comment();
    frm.dashboard.add_comment(
        __('Assignment Condition Preview: {0}', [condition]), 
        'blue', 
        true
    );
    
    // Show real-time alert
    frappe.show_alert({
        message: __('Assignment condition will be: {0}', [condition]),
        indicator: 'blue'
    });
} 