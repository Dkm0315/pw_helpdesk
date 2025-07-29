frappe.ui.form.on('HD Category', {
    refresh: function(frm) {
        // Add custom buttons only for main categories
        if (!frm.doc.is_sub_category) {
            frm.add_custom_button(__('Get Sub Categories'), function() {
                frm.call({
                    method: 'get_sub_categories',
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint({
                                title: __('Sub Categories'),
                                message: frappe.render_template('sub_categories_list', {sub_categories: r.message}),
                                indicator: 'green'
                            });
                        }
                    }
                });
            });
        }

        frm.add_custom_button(__('Assignment Info'), function() {
            frm.call({
                method: 'get_assignment_info',
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint({
                            title: __('Assignment Information'),
                            message: frappe.render_template('assignment_info', {info: r.message}),
                            indicator: 'blue'
                        });
                    }
                }
            });
        });

        if (frm.doc.enable_escalation) {
            frm.add_custom_button(__('Escalation Info'), function() {
                frm.call({
                    method: 'get_escalation_info',
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint({
                                title: __('Escalation Information'),
                                message: frappe.render_template('escalation_info', {info: r.message}),
                                indicator: 'orange'
                            });
                        }
                    }
                });
            });
        }
    },

    is_sub_category: function(frm) {
        // Show/hide parent category field based on is_sub_category
        frm.toggle_display('parent_category', frm.doc.is_sub_category);
        
        // Clear parent category if not a sub-category
        if (!frm.doc.is_sub_category) {
            frm.set_value('parent_category', '');
        }
    },

    parent_category: function(frm) {
        // Auto-generate category code based on parent category
        if (frm.doc.parent_category && frm.doc.category_name) {
            frm.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'HD Category',
                    name: frm.doc.parent_category
                },
                callback: function(r) {
                    if (r.message) {
                        let parent_code = r.message.category_code;
                        let sub_name = frm.doc.category_name.replace(/\s+/g, '_').toUpperCase();
                        frm.set_value('category_code', `${parent_code}_${sub_name}`);
                    }
                }
            });
        }
    },

    category_name: function(frm) {
        // Auto-generate category code if not provided
        if (!frm.doc.category_code && frm.doc.category_name) {
            let code = frm.doc.category_name.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
            if (code.length > 10) {
                code = code.substring(0, 10);
            }
            frm.set_value('category_code', code);
        }
    },

    enable_escalation: function(frm) {
        // Show/hide escalation fields based on enable_escalation
        let escalation_fields = [
            'escalation_type',
            'escalation_1_point',
            'escalation_1_unit',
            'escalation_1_assignee',
            'escalation_2_point',
            'escalation_2_unit',
            'escalation_2_assignee',
            'escalation_3_point',
            'escalation_3_unit',
            'escalation_3_assignee'
        ];

        escalation_fields.forEach(field => {
            frm.toggle_display(field, frm.doc.enable_escalation);
        });
    },

    assign_issue_to_user: function(frm) {
        // Show/hide assignee field based on assign_issue_to_user
        frm.toggle_display('assignee', frm.doc.assign_issue_to_user);
    },

    assign_issue_to_permission_role_holder: function(frm) {
        // Show/hide permission role holder field
        frm.toggle_display('permission_role_holder', frm.doc.assign_issue_to_permission_role_holder);
    },

    validate: function(frm) {
        // Client-side validation
        if (frm.doc.enable_escalation && !frm.doc.escalation_type) {
            frappe.msgprint(__('Please select an escalation type when escalation is enabled.'));
            return false;
        }

        if (frm.doc.assign_issue_to_user && !frm.doc.assignee) {
            frappe.msgprint(__('Please provide assignee email addresses when "Assign Issue To User" is enabled.'));
            return false;
        }

                if (frm.doc.assign_issue_to_permission_role_holder && !frm.doc.permission_role_holder) {
            frappe.msgprint(__('Please provide permission role holder when "Assign Issue to Permission Role Holder" is enabled.'));
            return false;
        }

        // Validate sub-category settings
        if (frm.doc.is_sub_category && !frm.doc.parent_category) {
            frappe.msgprint(__('Please select a parent category when "Is Sub Category" is checked.'));
            return false;
        }
    }
});

// Template for sub categories list
frappe.templates['sub_categories_list'] = `
<div class="sub-categories-list">
    <h4>Sub Categories</h4>
    {% if sub_categories.length %}
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Code</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                {% for sub_cat in sub_categories %}
                <tr>
                    <td>{{ sub_cat.sub_category_name }}</td>
                    <td>{{ sub_cat.sub_category_code }}</td>
                    <td>{{ sub_cat.description || '-' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    {% else %}
        <p>No sub categories found.</p>
    {% endif %}
</div>
`;

// Template for assignment info
frappe.templates['assignment_info'] = `
<div class="assignment-info">
    <h4>Assignment Information</h4>
    <table class="table table-bordered">
        <tr>
            <td><strong>Assign Issue To User:</strong></td>
            <td>{{ info.assign_issue_to_user ? 'Yes' : 'No' }}</td>
        </tr>
        <tr>
            <td><strong>Assignee:</strong></td>
            <td>{{ info.assignee || 'Not specified' }}</td>
        </tr>
        <tr>
            <td><strong>Assign Issue to External Vendor:</strong></td>
            <td>{{ info.assign_issue_to_external_vendor ? 'Yes' : 'No' }}</td>
        </tr>
        <tr>
            <td><strong>Assign Issue to Permission Role Holder:</strong></td>
            <td>{{ info.assign_issue_to_permission_role_holder ? 'Yes' : 'No' }}</td>
        </tr>
        <tr>
            <td><strong>Permission Role Holder:</strong></td>
            <td>{{ info.permission_role_holder || 'Not specified' }}</td>
        </tr>
    </table>
</div>
`;

// Template for escalation info
frappe.templates['escalation_info'] = `
<div class="escalation-info">
    <h4>Escalation Information</h4>
    <table class="table table-bordered">
        <tr>
            <td><strong>Escalation Type:</strong></td>
            <td>{{ info.escalation_type }}</td>
        </tr>
        <tr>
            <td><strong>Level 1:</strong></td>
            <td>{{ info.escalation_1.point }} {{ info.escalation_1.unit }} - {{ info.escalation_1.assignee || 'Not specified' }}</td>
        </tr>
        <tr>
            <td><strong>Level 2:</strong></td>
            <td>{{ info.escalation_2.point }} {{ info.escalation_2.unit }} - {{ info.escalation_2.assignee || 'Not specified' }}</td>
        </tr>
        <tr>
            <td><strong>Level 3:</strong></td>
            <td>{{ info.escalation_3.point }} {{ info.escalation_3.unit }} - {{ info.escalation_3.assignee || 'Not specified' }}</td>
        </tr>
    </table>
</div>
`; 