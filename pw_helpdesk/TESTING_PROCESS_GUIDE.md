# 🧪 PW Helpdesk Testing Process Guide

## 📋 Overview of System Architecture

### **How the Components Connect:**
```
HD Category → HD Service Level Agreement → Assignment Rule → Dynamic User Assignment → Users → HD Agents
     ↓              ↓                         ↓                     ↓                  ↓         ↓
   Ticket      Auto SLA Applied          Auto Agent           Condition-based    Create     Assign
 Creation       + Team Assigned          Assignment            User Selection    Agents     Tickets
```

## 🛠️ **STEP-BY-STEP TESTING PROCESS**

### **Phase 1: Setup Foundation Data**

#### **Step 1: Create HD Teams**
```bash
# Go to: Helpdesk → Setup → HD Team
```
- Create teams like:
  - "Technical Support Team"
  - "Billing Support Team" 
  - "HR Support Team"

#### **Step 2: Create Users (if needed)**
```bash
# Go to: Users and Permissions → User
```
- Ensure you have test users for different roles
- Note their email addresses for later assignment

#### **Step 3: Create Dynamic User Assignment**
```bash
# Go to: CN HRMS Core → Dynamic User Assignment
```
- **Name**: "Tech Support Assignment"
- **Users Table**: Add 2-3 users who should handle technical tickets
- **Conditions**: Set any conditions (or leave blank for all)

#### **Step 4: Verify HD Categories**
```bash
# Go to: Helpdesk → Setup → HD Category
```
- Confirm categories exist (AI_AM_1, ACC_HR-1, etc.)
- Note the category names for testing

### **Phase 2: Apply Custom Fields Manually**

#### **Step 5: Add Custom Fields to HD Service Level Agreement**
```bash
# Go to: Settings → Customize Form → HD Service Level Agreement
```

**Add these 3 custom fields:**

1. **Field 1: Applicable Categories**
   - Label: "Applicable Categories"
   - Type: "Table MultiSelect"
   - Options: "HD Category MultiSelect"
   - Insert After: "Default SLA" or similar

2. **Field 2: Auto Assign Team**
   - Label: "Auto Assign Team"  
   - Type: "Link"
   - Options: "HD Team"
   - Insert After: "Applicable Categories"

3. **Field 3: Assignment Rule**
   - Label: "Assignment Rule"
   - Type: "Link" 
   - Options: "Assignment Rule"
   - Insert After: "Auto Assign Team"

#### **Step 6: Add Custom Field to Assignment Rule**
```bash
# Go to: Settings → Customize Form → Assignment Rule
```

**Add this field:**
- **Label**: "User Assignment"
- **Type**: "Link"
- **Options**: "Dynamic User Assignment"  
- **Insert After**: "Field" (in Assignment Conditions section)
- **Depends On**: `eval: doc.rule == 'Based on Field'`

### **Phase 3: Create Assignment Rule**

#### **Step 7: Create Assignment Rule**
```bash
# Go to: Settings → Assignment Rule
```
- **Rule Name**: "Technical Support Auto Assignment"
- **Document Type**: "HD Ticket"
- **Rule**: "Based on Field"
- **Field**: "custom_category" 
- **Value**: "AI_AM_1" (or your test category)
- **User Assignment**: Select "Tech Support Assignment" (from Step 3)
- **Enabled**: ✅ Check

### **Phase 4: Create Service Level Agreement**

#### **Step 8: Create SLA with Categories**
```bash
# Go to: Helpdesk → Setup → HD Service Level Agreement
```

⚠️ **Important**: SLA creation requires several mandatory tables. Here's the minimum setup:

**Basic Info:**
- **Service Level Name**: "Standard Tech Support SLA"
- **Enabled**: ✅ Check
- **Default SLA**: ✅ Check (if no other SLA exists)

**Custom Fields** (our additions):
- **Applicable Categories**: Add "AI_AM_1" (AC Issue category)
- **Auto Assign Team**: Select "Technical Support Team"
- **Assignment Rule**: Select "Technical Support Auto Assignment"

**Required Tables** (minimum entries):
1. **Priorities Table**: Add at least one priority (e.g., Medium, 2 hours response, 24 hours resolution)
2. **SLA Fulfilled On**: Add "Resolved" status
3. **Working Hours**: Add at least Monday-Friday 9-5
4. **Holiday List**: Create or select a holiday list

### **Phase 5: Test the Complete Workflow**

#### **Step 9: Create Test Ticket**
```bash
# Go to: Helpdesk → HD Ticket → New
```

**Create ticket with:**
- **Subject**: "Test AC Unit Not Working"
- **Description**: "Testing automatic SLA assignment"
- **Category**: Select "AI_AM_1" (AC Issue)
- **Priority**: "Medium"

#### **Step 10: Verify Automation Results**

**Check these automatically applied:**
1. **SLA Applied**: Should show "Standard Tech Support SLA"
2. **Team Assigned**: Should show "Technical Support Team" 
3. **Agents Assigned**: Check if users from Dynamic User Assignment are assigned
4. **HD Agent Records**: Verify HD Agent records were created for assigned users

### **Phase 6: Advanced Testing**

#### **Step 11: Test Different Categories**
- Create tickets with different categories
- Verify different SLAs apply (if configured)
- Test fallback behavior when no SLA matches

#### **Step 12: Test Form Script Features**
- Change category on existing ticket
- Verify real-time SLA application
- Test "Check SLA Status" button (if visible)

#### **Step 13: Test API Functions**
```bash
# Go to: Developer Console or API testing tool
```

Test these API calls:
```javascript
// Check applicable SLA for category
frappe.call({
    method: 'pw_helpdesk.customizations.api.sla_management.get_applicable_sla',
    args: { category: 'AI_AM_1' }
});

// Check SLA status for ticket
frappe.call({
    method: 'pw_helpdesk.customizations.api.sla_management.check_sla_status', 
    args: { ticket_id: 'HD-TICKET-ID', category: 'AI_AM_1' }
});
```

## 🔍 **Verification Checklist**

### **✅ What Should Happen Automatically:**

| Step | Expected Result | Where to Check |
|------|----------------|----------------|
| Ticket Created with Category | SLA Auto-Applied | Ticket → SLA field |
| SLA Applied | Team Auto-Assigned | Ticket → Agent Group field |
| Team Assigned | Agents Auto-Assigned | Ticket → Assignments section |
| Users Assigned | HD Agent Records Created | HD Agent list |
| Category Changed | New SLA Applied | Real-time form update |

### **🚨 Troubleshooting**

**If SLA doesn't auto-apply:**
- Check if category is in SLA's "Applicable Categories"
- Verify SLA is enabled
- Check console for any errors

**If team doesn't auto-assign:**
- Verify "Auto Assign Team" field is set in SLA
- Check if team exists and is active

**If agents don't auto-assign:**
- Verify Assignment Rule is enabled
- Check Dynamic User Assignment has users
- Verify users exist and are enabled

**If HD Agent records not created:**
- Check user permissions
- Look for error logs in Error Log doctype

## 🎯 **Expected End-to-End Flow**

1. **User creates ticket** with category "AI_AM_1"
2. **System finds** "Standard Tech Support SLA" (contains AI_AM_1 category)
3. **SLA applied** automatically to ticket
4. **Team assigned** from SLA config ("Technical Support Team")
5. **Assignment Rule triggers** ("Technical Support Auto Assignment")
6. **Dynamic User Assignment** provides list of users
7. **Users assigned** to ticket automatically
8. **HD Agent records** created for users (if not existing)
9. **User sees** toast notification about SLA application

## 🚀 **Success Criteria**

The system is working correctly when:
- ✅ Tickets get SLA applied automatically based on category
- ✅ Teams get assigned from SLA configuration
- ✅ Agents get assigned based on Dynamic User Assignment
- ✅ HD Agent records are created automatically
- ✅ Users receive real-time feedback about assignments
- ✅ Different categories trigger different SLAs/teams

---
**Testing Duration**: ~30-45 minutes for complete setup and testing  
**Complexity**: Medium (requires understanding of Frappe form customization)  
**Result**: Full automated helpdesk workflow with category-based SLA assignment 