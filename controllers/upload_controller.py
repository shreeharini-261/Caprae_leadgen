import pandas as pd
import io
import re
from datetime import datetime
from models.lead_model import db, Lead
import chardet
from flask import flash

class UploadController:
    @staticmethod
    def log_error(filename, row_number, data, reason):
        log_file = "upload_errors.log"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_file, "a", encoding='utf-8') as f:
            f.write(f"[{timestamp}] {filename} Row {row_number}: {reason} ")
            f.write(f"Data: {data}\n")

    @staticmethod
    def write_log_separator(filename):
        log_file = "upload_errors.log"
        with open(log_file, "a", encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"New Upload Session - File: {filename} at {timestamp}\n")

    @staticmethod
    def clean_email(email):
        if pd.isna(email):
            return None
        return str(email).strip().lower()

    @staticmethod
    def clean_phone(phone):
        if pd.isna(phone):
            return None
        return re.sub(r'\D', '', str(phone))
    
    @staticmethod
    def clean_website(website):
        if pd.isna(website):
            return None
        return str(website).strip().lower()

    @staticmethod
    def is_valid_email(email):
        if not email or pd.isna(email):
            return False
        EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
        return bool(EMAIL_REGEX.match(str(email).strip()))

    @staticmethod
    def is_valid_phone(phone):
        if not phone or pd.isna(phone):
            return False
        phone_str = re.sub(r'\D', '', str(phone))
        return phone_str.isdigit() and len(phone_str) >= 8
    
    @staticmethod
    def is_valid_website(website):
        if not website or pd.isna(website):
            return False
        return bool(website.strip())

    @staticmethod
    def is_valid_row(name, email, phone):
        return bool(name and str(name).strip()) and UploadController.is_valid_email(email) and UploadController.is_valid_phone(phone)

    @staticmethod
    def process_csv_file(file, name_col, email_col, phone_col, dynamic_fields=None, first_name_col=None, last_name_col=None):
        filename = file.filename
        UploadController.write_log_separator(filename)

        try:
            content = file.read()

            # Robust encoding detection and decoding
            if isinstance(content, bytes):
                detection = chardet.detect(content)
                detected_encoding = detection['encoding']
                encodings_to_try = [detected_encoding, 'utf-8', 'latin-1', 'windows-1252', 'ISO-8859-1']
                for encoding in encodings_to_try:
                    if not encoding:
                        continue
                    try:
                        content = content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise Exception("Could not decode the file with any common encoding")

            df = pd.read_csv(io.StringIO(content))
            df.columns = df.columns.str.strip()

            missing_cols = [col for col in [email_col, phone_col] if col not in df.columns]
            if missing_cols:
                raise Exception(f"Missing required columns: {', '.join(missing_cols)}")

            # Handle first_name and last_name columns if provided
            if first_name_col and first_name_col in df.columns:
                df['first_name'] = df[first_name_col].fillna("").astype(str).str.strip()
            if last_name_col and last_name_col in df.columns:
                df['last_name'] = df[last_name_col].fillna("").astype(str).str.strip()

            # Only process name if name_col is provided and exists in columns
            if name_col and name_col in df.columns:
                df[name_col] = df[name_col].fillna("")
                df['name'] = df[name_col].astype(str).str.strip()
                def split_name(name):
                    if not name or pd.isna(name):
                        return "", ""
                    parts = name.strip().split()
                    if len(parts) == 0:
                        return "", ""
                    elif len(parts) == 1:
                        return parts[0], ""
                    else:
                        return parts[0], " ".join(parts[1:])
                df['first_name'], df['last_name'] = zip(*df['name'].map(split_name))
            else:
                if 'first_name' not in df.columns:
                    df['first_name'] = ""
                if 'last_name' not in df.columns:
                    df['last_name'] = ""
                df['name'] = ""

            # Always set name to first_name + last_name if name is empty
            df['name'] = df.apply(lambda row: row['name'] if 'name' in row and row['name'] else f"{row.get('first_name','')} {row.get('last_name','')}".strip(), axis=1)

            df['email'] = df[email_col].apply(UploadController.clean_email)
            df['phone'] = df[phone_col].apply(UploadController.clean_phone)

            added = 0
            skipped_duplicates = 0
            errors = 0
            skipped_details = []

            for idx, row in df.iterrows():
                name = row['name']
                email = row['email']
                phone = row['phone']
                first_name = row['first_name']
                last_name = row['last_name']

                if not UploadController.is_valid_row(name, email, phone):
                    errors += 1
                    reason = "Invalid row: Missing or invalid required fields"
                    UploadController.log_error(
                        filename,
                        idx + 2,  # Adding 2 to account for 0-based index and header row
                        {
                            'name': name,
                            'email': email,
                            'phone': phone
                        },
                        reason
                    )
                    skipped_details.append(f"Row {idx+2}: {reason}")
                    continue

                existing_lead = Lead.query.filter(
                    (Lead.email == email) | (Lead.phone == phone)
                ).first()

                if existing_lead:
                    skipped_duplicates += 1
                    reason = "Duplicate entry found"
                    UploadController.log_error(
                        filename,
                        idx + 2,
                        {
                            'name': name,
                            'email': email,
                            'phone': phone
                        },
                        reason
                    )
                    skipped_details.append(f"Row {idx+2}: {reason}")
                    continue

                try:
                    lead_data = {
                        'first_name': str(first_name).strip() if first_name is not None else '',
                        'last_name': str(last_name).strip() if last_name is not None else '',
                        'email': str(email).strip() if email is not None else '',
                        'phone': str(phone).strip() if phone is not None else ''
                    }
                    # Add dynamic fields
                    if dynamic_fields:
                        for db_field, csv_col in dynamic_fields.items():
                            if csv_col in df.columns:
                                value = row[csv_col]
                                lead_data[db_field] = str(value).strip() if value is not None else ''
                    # Truncate only the fields defined in the model
                    lead_data = Lead.truncate_fields(lead_data)

                    # Use smart add/update logic
                    from controllers.lead_controller import LeadController
                    success, msg = LeadController.add_or_update_lead_by_match(lead_data)
                    if success:
                        added += 1
                    else:
                        skipped_duplicates += 1
                        skipped_details.append(f"Row {idx+2}: {msg}")
                except Exception as e:
                    errors += 1
                    reason = f"Database error: {str(e)}"
                    UploadController.log_error(
                        filename,
                        idx + 2,
                        {
                            'name': name,
                            'email': email,
                            'phone': phone
                        },
                        reason
                    )
                    skipped_details.append(f"Row {idx+2}: {reason}")
                    continue

            # Don't flash skipped details
            # if skipped_details:
            #     flash(' / '.join(skipped_details), 'info')

            return added, skipped_duplicates, errors

        except pd.errors.EmptyDataError:
            UploadController.log_error(filename, 0, {}, "The CSV file is empty")
            raise Exception("The CSV file is empty")
        except pd.errors.ParserError:
            UploadController.log_error(filename, 0, {}, "Invalid CSV format")
            raise Exception("Invalid CSV format")
        except Exception as e:
            UploadController.log_error(filename, 0, {}, f"Error processing CSV: {str(e)}")
            raise Exception(f"Error processing CSV: {str(e)}")