# WhatsApp Bulk Sender

A professional Flask application to send bulk WhatsApp messages with personalization.

## Features

✅ **Modern Web Interface** - Beautiful, responsive design  
✅ **Bulk Messaging** - Send to multiple contacts at once  
✅ **International Support** - Phone numbers with country codes (+91, +1, +44, etc.)  
✅ **CSV Upload & Live Editing** - Upload CSV and edit contacts before sending  
✅ **Personalization** - Use {name} placeholder in messages  
✅ **Real-time Status** - Monitor sending progress live  
✅ **Scheduled Messages** - Set specific date/time for each message  
✅ **Error Handling** - Comprehensive error tracking  

## Installation

1. Install Python 3.8 or higher

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the server:

   ```bash
   python app.py
   ```

2. Open browser: `http://localhost:5000`

3. **Upload CSV** or **manually add contacts**

### CSV Format

Your CSV should have 3 columns (with header row):

```csv
Name,Phone,Send
John Doe,+919876543210,1
Jane Smith,+14155551234,0
Bob Wilson,+447911123456,1
```

- **Name**: Contact name
- **Phone**: Phone number WITH country code (e.g., +919876543210, +14155551234)
- **Send**: 1 = Send message, 0 = Skip

4. Preview and edit contacts in the table

5. Configure messages (use {name} for personalization)

6. Set wait time between messages

7. Click "Start Sending"

8. Monitor progress on status page

## Important Notes

⚠️ **WhatsApp Web**: Make sure WhatsApp Web is logged in  
⚠️ **Phone Format**: MUST include country code with + sign (e.g., +919876543210)  
⚠️ **Send Flag**: Use 1 to send, 0 to skip  
⚠️ **Timing**: Messages are sent with delays to avoid spam detection  
⚠️ **Testing**: Test with small batches first  

## Phone Number Examples

**Correct formats:**

- India: `+919876543210`
- USA: `+14155551234`
- UK: `+447911123456`
- Australia: `+61412345678`

**Must include:**

- Plus sign (+)
- Country code
- Full phone number

## Configuration

- **Wait Time**: Delay between messages (5-60 seconds, default: 10)
- **Send Flag**: 1 = Send, 0 = Don't send

## Troubleshooting

**Messages not sending?**

- Ensure WhatsApp Web is logged in
- Verify phone numbers include + and country code
- Check Send flag is 1 (not 0)
- Increase wait time if needed

**Job fails?**

- Check logs for error details
- Verify pywhatkit is installed correctly
- Ensure browser automation is allowed

## License

MIT License - Free to use and modify
