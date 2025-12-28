import json
import time
from datetime import datetime
import pywhatkit as kit
import pyautogui
import keyboard


def run_send_job(params, logger):
    """
    Main function to send WhatsApp messages based on parameters
    """
    logger("🚀 Starting send job...")
    
    # Extract parameters
    rows = params['edited_rows']
    messages_db_file = params['messages_db']
    template_key = params['template_key']
    name_col = params['name_col']
    phone_col = params['phone_col']
    flag_col = params['flag_col']
    country_code = params.get('country_code', '+91')
    wait_time = params['wait_time']
    use_country_code = params.get('use_country_code', True)
    
    # Load messages
    try:
        with open(messages_db_file, 'r', encoding='utf-8') as f:
            messages_db = json.load(f)
        
        if template_key not in messages_db:
            logger(f"❌ Template key '{template_key}' not found in messages database")
            return
        
        messages = messages_db[template_key]
        logger(f"📋 Loaded {len(messages)} message templates")
    except Exception as e:
        logger(f"❌ Error loading messages: {e}")
        return
    
    # Process rows
    logger(f"📊 Processing {len(rows)} contacts...")
    sent_count = 0
    skip_count = 0
    error_count = 0
    
    for idx, row in enumerate(rows, 1):
        try:
            # Validate row data
            if len(row) <= max(name_col, phone_col, flag_col):
                logger(f"⚠️ Row {idx}: Invalid row format, skipping")
                skip_count += 1
                continue
            
            name = str(row[name_col]).strip()
            phone = str(row[phone_col]).strip()
            flag = str(row[flag_col]).strip()
            
            # Check if should send (0 = No, 1 = Yes)
            if flag not in ['1', 'Y', 'YES', 'y', 'yes']:
                logger(f"⏭️ Row {idx}: Skipping {name} (flag: {flag})")
                skip_count += 1
                continue
            
            # Process phone number
            # If phone already has country code (starts with + or is international format)
            if phone.startswith('+'):
                full_phone = phone
                logger(f"📞 Using phone with country code: {full_phone}")
            elif use_country_code:
                # Clean phone number and add default country code
                phone_clean = ''.join(filter(str.isdigit, phone))
                if not phone_clean:
                    logger(f"❌ Row {idx}: Invalid phone number for {name}")
                    error_count += 1
                    continue
                full_phone = f"{country_code}{phone_clean}"
                logger(f"📞 Added country code: {full_phone}")
            else:
                # Phone number should already include country code
                if not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                    logger(f"❌ Row {idx}: Invalid phone number format for {name}")
                    error_count += 1
                    continue
                # Ensure it starts with +
                if not phone.startswith('+'):
                    full_phone = '+' + ''.join(filter(str.isdigit, phone))
                else:
                    full_phone = phone
            
            # Send messages
            for msg_idx, msg_data in enumerate(messages, 1):
                try:
                    template = msg_data['template']
                    # Replace placeholders
                    message = template.replace('{name}', name).replace('{Name}', name)
                    
                    logger(f"📤 Row {idx}, Msg {msg_idx}: Sending to {name} ({full_phone})")
                    
                    # Get current time for immediate send
                    now = datetime.now()
                    hour = now.hour
                    minute = now.minute + 1  # Send 1 minute from now
                    
                    # Send via WhatsApp
                    kit.sendwhatmsg(full_phone, message, hour, minute, wait_time, True, 2)
                    
                    logger(f"✅ Sent message {msg_idx} to {name}")
                    sent_count += 1
                    
                    # Wait between messages
                    time.sleep(wait_time)
                    
                    # Press ESC to close WhatsApp Web tab
                    keyboard.press_and_release('esc')
                    time.sleep(1)
                    
                except Exception as e:
                    logger(f"❌ Error sending message {msg_idx} to {name}: {str(e)}")
                    error_count += 1
                    
        except Exception as e:
            logger(f"❌ Error processing row {idx}: {str(e)}")
            error_count += 1
    
    # Summary
    logger("=" * 50)
    logger(f"✅ Job completed!")
    logger(f"📊 Total contacts: {len(rows)}")
    logger(f"✅ Messages sent: {sent_count}")
    logger(f"⏭️ Skipped: {skip_count}")
    logger(f"❌ Errors: {error_count}")
    logger("=" * 50)
