import json
import time
from datetime import datetime
import pywhatkit as kit
import keyboard


def run_send_job(params, logger):
    """
    Main function to send WhatsApp messages based on filter combinations
    """
    logger("🚀 Starting send job...")
    
    rows = params['rows']
    headers = params['headers']
    filter_messages = params['filter_messages']
    wait_time = params['wait_time']
    
    # Find Name and Phone column indices
    name_col_idx = 0
    phone_col_idx = 1
    
    logger(f"📋 Headers: {', '.join(headers)}")
    logger(f"📊 Total contacts: {len(rows)}")
    logger(f"🎯 Total filter combinations: {len(filter_messages)}")
    
    sent_count = 0
    skip_count = 0
    error_count = 0
    
    # Track summary by filter
    filter_summary = []
    for idx, fm in enumerate(filter_messages):
        filter_summary.append({
            'filter_id': idx + 1,
            'filters': fm['filters'],
            'sent': 0,
            'skipped': 0
        })
    
    for row_idx, row in enumerate(rows, 1):
        try:
            if len(row) < 2:
                logger(f"⚠️ Row {row_idx}: Invalid row format, skipping")
                skip_count += 1
                continue
            
            name = row[name_col_idx].strip()
            phone = row[phone_col_idx].strip()
            
            if not name or not phone:
                logger(f"⚠️ Row {row_idx}: Missing name or phone, skipping")
                skip_count += 1
                continue
            
            # Ensure phone has country code
            if not phone.startswith('+'):
                logger(f"⚠️ Row {row_idx}: Phone {phone} missing country code, skipping")
                skip_count += 1
                continue
            
            logger(f"\n{'='*60}")
            logger(f"👤 Contact {row_idx}: {name} ({phone})")
            
            # Check which filter combinations match this contact
            messages_to_send = []
            
            for filter_idx, filter_msg in enumerate(filter_messages):
                filters = filter_msg['filters']
                match = True
                
                logger(f"   🔍 Checking Filter #{filter_idx + 1}:")
                
                # Check each category filter
                for category, required_value in filters.items():
                    col_idx = headers.index(category) if category in headers else -1
                    
                    if col_idx == -1 or col_idx >= len(row):
                        logger(f"      ❌ {category}: Column not found")
                        match = False
                        break
                    
                    cell_value = str(row[col_idx]).strip()
                    
                    if cell_value.upper() != required_value.upper():
                        logger(f"      ❌ {category}: Expected '{required_value}', Got '{cell_value}'")
                        match = False
                        break
                    else:
                        logger(f"      ✅ {category}: {cell_value} (matches)")
                
                if match:
                    logger(f"   ✅ Filter #{filter_idx + 1} MATCHED - Message will be sent")
                    messages_to_send.append({
                        'filter_id': filter_idx + 1,
                        'message': filter_msg['template'],
                        'datetime': filter_msg['send_datetime'],
                        'filters': filters
                    })
                    filter_summary[filter_idx]['sent'] += 1
                else:
                    logger(f"   ⏭️ Filter #{filter_idx + 1} NOT MATCHED - Skipping")
                    filter_summary[filter_idx]['skipped'] += 1
            
            if not messages_to_send:
                logger(f"   ℹ️ No matching filters for {name}")
                skip_count += 1
                continue
            
            # Send messages for each matched filter
            for msg_data in messages_to_send:
                try:
                    filter_id = msg_data['filter_id']
                    template = msg_data['message']
                    
                    # Replace placeholders
                    message = template.replace('{name}', name).replace('{Name}', name)
                    
                    logger(f"   📤 Sending Filter #{filter_id} message to {name}...")
                    
                    # Get current time for immediate send
                    now = datetime.now()
                    hour = now.hour
                    minute = now.minute + 1
                    
                    # Send via WhatsApp
                    kit.sendwhatmsg(phone, message, hour, minute, wait_time, True, 2)
                    
                    logger(f"   ✅ Filter #{filter_id} message sent successfully!")
                    sent_count += 1
                    
                    # Wait between messages
                    time.sleep(wait_time)
                    
                    # Press ESC to close tab
                    keyboard.press_and_release('esc')
                    time.sleep(1)
                    
                except Exception as e:
                    logger(f"   ❌ Error sending Filter #{filter_id} message: {str(e)}")
                    error_count += 1
                    
        except Exception as e:
            logger(f"❌ Error processing row {row_idx}: {str(e)}")
            error_count += 1
    
    # Summary
    logger("\n" + "=" * 60)
    logger("📊 SUMMARY REPORT")
    logger("=" * 60)
    logger(f"👥 Total contacts processed: {len(rows)}")
    logger(f"✅ Messages sent: {sent_count}")
    logger(f"⏭️ Skipped: {skip_count}")
    logger(f"❌ Errors: {error_count}")
    logger("\n🎯 FILTER BREAKDOWN:")
    for summary in filter_summary:
        filter_desc = ", ".join([f"{k}={v}" for k, v in summary['filters'].items()])
        logger(f"   Filter #{summary['filter_id']} ({filter_desc}): {summary['sent']} sent, {summary['skipped']} skipped")
    logger("=" * 60)
