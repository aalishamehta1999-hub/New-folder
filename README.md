# WhatsApp Bulk Sender - Dynamic Category System

A professional Flask application to send bulk WhatsApp messages with dynamic category-based messaging.

## Features

✅ **Dynamic Categories** - Automatically detects all columns as categories (Mehendi, Sangeet, Wedding, etc.)  
✅ **Smart Filtering** - Send messages only to selected categories (Yes/No)  
✅ **Live Summary** - See how many contacts in each category  
✅ **CSV & Excel Support** - Upload CSV or Excel (.xlsx, .xls) files  
✅ **Live Editing** - Edit contacts and categories before sending  
✅ **Personalization** - Use {name} placeholder in messages  
✅ **Real-time Status** - Monitor sending progress live  
✅ **Category Reports** - Detailed breakdown by category  

## Installation

1. Install Python 3.8 or higher

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create sample file:

   ```bash
   python create_sample_excel.py
   ```

## File Format

Your file should have minimum 2 columns (Name, Phone) + any number of category columns:

**Excel Format (.xlsx/.xls):**

| Name   | Phone        | Mehendi | Sangeet | Wedding | Reception |
|--------|--------------|---------|---------|---------|-----------|
| Ganesh | +919876543210 | Yes     | Yes     | Yes     | Yes       |
| Priya  | +918765432109 | No      | Yes     | Yes     | Yes       |
| Rahul  | +917654321098 | Yes     | No      | Yes     | Yes       |

**CSV Format:**

```csv
Name,Phone,Mehendi,Sangeet,Wedding,Reception
Ganesh,+919876543210,Yes,Yes,Yes,Yes
Priya,+918765432109,No,Yes,Yes,Yes
Rahul,+917654321098,Yes,No,Yes,Yes
```

- **Name**: Contact name (Column 1)
- **Phone**: Phone WITH country code (Column 2, e.g., +919876543210)
- **Categories**: Any additional columns (Yes/No for each)

## Usage

1. **Start server:**

   ```bash
   python app.py
   ```

2. **Open browser:** `http://localhost:5000`

3. **Upload file** - System automatically detects categories

4. **Review summary** - See contact count per category

5. **Edit data** - Modify contacts/categories if needed

6. **Configure messages** - Set message for each category

7. **Start sending** - Monitor real-time progress

## How It Works

1. **Upload file** → System detects Name, Phone, and all category columns
2. **Summary shown** → See how many "Yes" in each category
3. **Configure messages** → One message template per category
4. **Smart sending** → Only sends to contacts with "Yes" in that category

Example:

- Ganesh has "Yes" for Mehendi → Gets Mehendi message
- Priya has "No" for Mehendi → Doesn't get Mehendi message
- Both have "Yes" for Wedding → Both get Wedding message

## Accepted Values

For category columns, these values mean **SEND MESSAGE**:

- `Yes`
- `Y`
- `1`

Any other value means **SKIP** (No, N, 0, blank, etc.)

## Important Notes

⚠️ **WhatsApp Web** - Must be logged in before starting  
⚠️ **Phone Format** - MUST include country code with + (e.g., +919876543210)  
⚠️ **First Row** - Must be header row (Name, Phone, Category1, Category2, ...)  
⚠️ **Categories** - All columns after Phone are treated as categories  
⚠️ **Testing** - Test with 2-3 contacts first  
